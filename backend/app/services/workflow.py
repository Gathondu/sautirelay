import logging
import secrets
from uuid import uuid4

from backend.app.core.config import get_settings
from backend.app.core.models import (
    ApproximateLocation,
    AuditLogDocument,
    AuthenticatedUser,
    ClusterStatus,
    DashboardMetrics,
    EscalationCreateRequest,
    EscalationDocument,
    EscalationStatus,
    OutcomeCreateRequest,
    OutcomeDocument,
    ReportCategory,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportDocument,
    ReportStatus,
    RiskLevel,
    SafeStatusResponse,
    SignalClusterDocument,
    VerificationDecision,
    VerificationDocument,
    VerificationRequest,
    utc_now,
)
from backend.app.repositories.memory import SautiRelayRepository
from backend.app.services.clustering import (
    DEFAULT_SIMILARITY_THRESHOLD,
    cosine_similarity,
)
from backend.app.services.intake_mapping import openai_intake_to_report_updates
from backend.app.services.openai_intake import OpenAIIntakeService
from fastapi import HTTPException, status


class WorkflowService:
    def __init__(self, repository: SautiRelayRepository) -> None:
        self._repository = repository
        self._logger = logging.getLogger(__name__)

    async def submit_report(self, request: ReportCreateRequest) -> ReportDocument:
        now = utc_now()
        report = ReportDocument.model_validate(
            {
                "report_id": self._id("report"),
                "tracking_code": self._tracking_code(),
                "submitted_at": now,
                "channel": request.channel,
                "language": request.language,
                "raw_text_encrypted": self._local_encrypted_placeholder(request.text),
                "redacted_text": None,
                "translated_text": None,
                "summary": None,
                "approximate_location": request.location,
                "raw_location_encrypted": self._local_encrypted_placeholder(request.location.model_dump_json()),
                "location_precision": request.location.location_precision,
                "category": request.category_hint,
                "urgency": request.timeframe,
                "risk_level": RiskLevel.high if request.immediate_danger else RiskLevel.medium,
                "confidence_score": 0.0,
                "reporter_anonymous": True,
                "status": ReportStatus.new,
                "created_at": now,
                "updated_at": now,
            }
        )
        await self._repository.put_report(report)
        await self._audit(None, "report.submitted", "report", report.id)
        return report

    def build_report_create_response(self, report: ReportDocument) -> ReportCreateResponse:
        return ReportCreateResponse.model_validate(
            {
                "report_id": report.id,
                "tracking_code": report.public_tracking_code,
                "status": report.status,
                "safe_status": self._safe_status(report.status),
                "message": "Your report has been received safely. Processing will continue in the background.",
            }
        )

    async def get_safe_status(self, tracking_code: str) -> SafeStatusResponse:
        report = await self._repository.get_report_by_tracking_code(tracking_code)
        if report is None:
            return SafeStatusResponse(tracking_code=tracking_code, status="Unable to verify")
        return SafeStatusResponse(tracking_code=tracking_code, status=self._safe_status(report.status))

    async def list_reports(self) -> list[ReportDocument]:
        return await self._repository.list_reports()

    async def get_report(self, report_id: str) -> ReportDocument:
        return await self._require_report(report_id)

    async def process_report(self, report_id: str, actor: AuthenticatedUser) -> ReportDocument:
        report = await self._require_report(report_id)
        if report.status == ReportStatus.processing:
            return report
        if report.status not in {ReportStatus.new, ReportStatus.processing}:
            return report
        report = await self._process_report_with_ai(report_id, actor_id=actor.id)
        await self._audit(actor.id, "report.processed", "report", report_id)
        return report

    async def process_report_in_background(self, report_id: str, actor_id: str | None = None) -> None:
        try:
            await self._process_report_with_ai(report_id, actor_id=actor_id)
        except HTTPException as exc:
            await self._handle_background_report_failure(report_id, str(exc.detail))
        except Exception as exc:  # pragma: no cover - defensive safety for background task failures
            await self._handle_background_report_failure(report_id, str(exc))

    async def _process_report_with_ai(self, report_id: str, actor_id: str | None) -> ReportDocument:
        settings = get_settings()
        if settings.environment != "test" and not settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI intake is not configured (set OPENAI_API_KEY).",
            )

        report = await self._require_report(report_id)
        now = utc_now()
        processing_report = report.model_copy(update={"status": ReportStatus.processing, "updated_at": now})
        await self._repository.put_report(processing_report)

        raw_text = self._restore_local_placeholder(processing_report.raw_text_encrypted)
        intake_service = OpenAIIntakeService()
        try:
            openai_result = intake_service.process_report(
                text=raw_text,
                language=processing_report.language,
                location=processing_report.approximate_location,
                category_hint=str(processing_report.category) if processing_report.category is not None else None,
                urgency_hint=str(processing_report.urgency) if processing_report.urgency is not None else None,
            )
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        updates = openai_intake_to_report_updates(openai_result)
        updated_report = processing_report.model_copy(
            update={
                **updates,
                "status": ReportStatus.pending_review,
                "updated_at": utc_now(),
            }
        )
        await self._repository.put_report(updated_report)
        await self._detach_report_from_clusters(report_id)
        reloaded = await self._require_report(report_id)
        await self._attach_to_cluster(reloaded)
        await self._audit(actor_id, "report.ai_processed", "report", report_id)
        return await self._require_report(report_id)

    async def verify_report(
        self,
        report_id: str,
        request: VerificationRequest,
        actor: AuthenticatedUser,
    ) -> ReportDocument | EscalationDocument:
        report = await self._require_report(report_id)
        verification = VerificationDocument.model_validate(
            {
                "id": self._id("verification"),
                "report_id": report.id,
                "cluster_id": None,
                "verifier_id": actor.id,
                "decision": request.decision,
                "notes": request.notes,
                "confidence": self._confidence_value(request.confidence),
                "adjusted_category": request.adjusted_category,
                "adjusted_risk_level": request.adjusted_risk_level,
                "adjusted_location": request.adjusted_location,
                "created_at": utc_now(),
            }
        )
        await self._repository.put_verification(verification)
        updated_report = self._apply_report_verification(report, request)
        await self._repository.put_report(updated_report)
        await self._audit(actor.id, "report.verified", "report", report.id, {"decision": str(request.decision)})
        if request.decision == VerificationDecision.escalate_immediately:
            escalation_request = EscalationCreateRequest()
            return await self._queue_escalation_from_report(updated_report, escalation_request, actor)
        return updated_report

    async def list_clusters(self) -> list[SignalClusterDocument]:
        return await self._repository.list_clusters()

    async def get_cluster(self, cluster_id: str) -> SignalClusterDocument:
        cluster = await self._repository.get_cluster(cluster_id)
        if cluster is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
        return cluster

    async def verify_cluster(
        self,
        cluster_id: str,
        request: VerificationRequest,
        actor: AuthenticatedUser,
    ) -> SignalClusterDocument:
        cluster = await self.get_cluster(cluster_id)
        verification = VerificationDocument.model_validate(
            {
                "id": self._id("verification"),
                "report_id": None,
                "cluster_id": cluster.id,
                "verifier_id": actor.id,
                "decision": request.decision,
                "notes": request.notes,
                "confidence": self._confidence_value(request.confidence),
                "adjusted_category": request.adjusted_category,
                "adjusted_risk_level": request.adjusted_risk_level,
                "adjusted_location": request.adjusted_location,
                "created_at": utc_now(),
            }
        )
        await self._repository.put_verification(verification)
        status_by_decision = {
            VerificationDecision.verified: ClusterStatus.verified,
            VerificationDecision.needs_more_info: ClusterStatus.pending_review,
            VerificationDecision.duplicate: ClusterStatus.archived,
            VerificationDecision.unverified_rumor: ClusterStatus.dismissed,
            VerificationDecision.dismissed: ClusterStatus.dismissed,
            VerificationDecision.archive: ClusterStatus.archived,
            VerificationDecision.archived: ClusterStatus.archived,
            VerificationDecision.escalate_immediately: ClusterStatus.verified,
        }
        updated_cluster = cluster.model_copy(
            update={
                "status": status_by_decision[request.decision],
                "category": request.adjusted_category or cluster.category,
                "risk_level": request.adjusted_risk_level or cluster.risk_level,
                "updated_at": utc_now(),
            }
        )
        await self._repository.put_cluster(updated_cluster)
        await self._audit(actor.id, "cluster.verified", "cluster", cluster.id, {"decision": str(request.decision)})
        return updated_cluster

    async def escalate_cluster(
        self,
        cluster_id: str,
        request: EscalationCreateRequest,
        actor: AuthenticatedUser,
    ) -> EscalationDocument:
        cluster = await self.get_cluster(cluster_id)
        if cluster.status != ClusterStatus.verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Cluster must be verified before escalation"
            )
        now = utc_now()
        escalation = EscalationDocument.model_validate(
            {
                "escalation_id": self._id("escalation"),
                "cluster_id": cluster.id,
                "report_id": None,
                "assigned_to": request.assigned_to,
                "assigned_organization": request.assigned_organization,
                "action_brief": "Mediator brief is being prepared. Please refresh shortly.",
                "safety_note": self._safe_mediator_note(request.safety_note),
                "urgency": request.urgency,
                "status": EscalationStatus.preparing_brief,
                "sent_at": now,
                "follow_up_due_at": request.follow_up_due_at,
                "created_at": now,
                "updated_at": now,
            }
        )
        updated_cluster = cluster.model_copy(update={"status": ClusterStatus.escalated, "updated_at": utc_now()})
        await self._repository.put_cluster(updated_cluster)
        await self._repository.put_escalation(escalation)
        await self._audit(actor.id, "cluster.escalation_queued", "cluster", cluster.id)
        return escalation

    async def finalize_cluster_escalation_brief(self, escalation_id: str, cluster_id: str, actor_id: str) -> None:
        try:
            cluster = await self.get_cluster(cluster_id)
            escalation = await self._require_escalation(escalation_id)
            request = EscalationCreateRequest.model_validate(
                {
                    "assigned_to": escalation.assigned_to,
                    "assigned_organization": escalation.assigned_organization,
                    "urgency": escalation.urgency,
                    "safety_note": escalation.safety_note,
                    "follow_up_due_at": escalation.follow_up_due_at,
                }
            )
            completed = self._build_escalation(cluster, None, request).model_copy(
                update={
                    "id": escalation.id,
                    "status": EscalationStatus.pending_acceptance,
                    "sent_at": escalation.sent_at,
                    "created_at": escalation.created_at,
                    "updated_at": utc_now(),
                }
            )
            await self._repository.put_escalation(completed)
            await self._audit(actor_id, "cluster.escalated", "cluster", cluster.id)
        except HTTPException as exc:
            await self._handle_background_escalation_failure(escalation_id, str(exc.detail), actor_id)
        except Exception as exc:  # pragma: no cover - defensive safety for background task failures
            await self._handle_background_escalation_failure(escalation_id, str(exc), actor_id)

    async def list_escalations(self, actor: AuthenticatedUser) -> list[EscalationDocument]:
        escalations = await self._repository.list_escalations()
        return [item for item in escalations if item.assigned_to in {actor.username, actor.id, "mediator-local-1"}]

    async def get_escalation(self, escalation_id: str, actor: AuthenticatedUser) -> EscalationDocument:
        escalation = await self._require_escalation(escalation_id)
        if escalation.assigned_to not in {actor.username, actor.id, "mediator-local-1"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Escalation is assigned to another mediator"
            )
        return escalation

    async def accept_escalation(self, escalation_id: str, actor: AuthenticatedUser) -> EscalationDocument:
        escalation = await self.get_escalation(escalation_id, actor)
        if escalation.status == EscalationStatus.preparing_brief:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Escalation brief is still being prepared. Please refresh shortly.",
            )
        updated = escalation.model_copy(
            update={"status": EscalationStatus.accepted, "accepted_at": utc_now(), "updated_at": utc_now()}
        )
        await self._repository.put_escalation(updated)
        await self._audit(actor.id, "escalation.accepted", "escalation", escalation.id)
        return updated

    async def record_outcome(
        self,
        escalation_id: str,
        request: OutcomeCreateRequest,
        actor: AuthenticatedUser,
    ) -> OutcomeDocument:
        escalation = await self.get_escalation(escalation_id, actor)
        now = utc_now()
        outcome = OutcomeDocument.model_validate(
            {
                "outcome_id": self._id("outcome"),
                "escalation_id": escalation.id,
                "outcome_type": request.outcome_type,
                "notes": request.notes,
                "deescalated": request.deescalated,
                "follow_up_required": request.follow_up_required,
                "recorded_by": actor.id,
                "created_at": now,
            }
        )
        next_status = EscalationStatus.follow_up_requested if request.follow_up_required else EscalationStatus.resolved
        resolved_at = None if request.follow_up_required else now
        updated_escalation = escalation.model_copy(
            update={"status": next_status, "resolved_at": resolved_at, "updated_at": now}
        )
        await self._repository.put_outcome(outcome)
        await self._repository.put_escalation(updated_escalation)
        await self._mark_related_reports_resolved(updated_escalation)
        await self._audit(actor.id, "outcome.recorded", "escalation", escalation.id)
        return outcome

    async def dashboard_metrics(self) -> DashboardMetrics:
        return await self._repository.dashboard_metrics()

    async def _require_report(self, report_id: str) -> ReportDocument:
        report = await self._repository.get_report(report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        return report

    async def _require_escalation(self, escalation_id: str) -> EscalationDocument:
        escalation = await self._repository.get_escalation(escalation_id)
        if escalation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")
        return escalation

    async def _detach_report_from_clusters(self, report_id: str) -> None:
        for cluster in await self._repository.list_clusters():
            if report_id not in cluster.report_ids:
                continue
            new_ids = [rid for rid in cluster.report_ids if rid != report_id]
            if not new_ids:
                await self._repository.delete_cluster(cluster.id)
            else:
                await self._repository.put_cluster(
                    cluster.model_copy(
                        update={
                            "report_ids": new_ids,
                            "report_count": len(new_ids),
                            "updated_at": utc_now(),
                        }
                    )
                )

    async def _attach_to_cluster(self, report: ReportDocument) -> None:
        region = self._region_from_location(report.approximate_location)
        now = utc_now()
        embedding = report.embedding or []
        all_reports = await self._repository.list_reports()

        if embedding and len(embedding) > 0:
            best_cluster_id: str | None = None
            best_similarity = 0.0
            for other in all_reports:
                if other.id == report.id:
                    continue
                other_vec = other.embedding or []
                if not other_vec or len(other_vec) != len(embedding):
                    continue
                if str(other.category) != str(report.category):
                    continue
                if self._region_from_location(other.approximate_location) != region:
                    continue
                sim = cosine_similarity(embedding, other_vec)
                if sim >= DEFAULT_SIMILARITY_THRESHOLD and sim > best_similarity and other.cluster_id:
                    best_similarity = sim
                    best_cluster_id = other.cluster_id

            if best_cluster_id:
                cluster = await self._repository.get_cluster(best_cluster_id)
                if cluster is not None and cluster.status in {
                    ClusterStatus.new,
                    ClusterStatus.pending_review,
                    ClusterStatus.verified,
                }:
                    report_ids = list(dict.fromkeys([*cluster.report_ids, report.id]))
                    updated_cluster = cluster.model_copy(
                        update={
                            "report_ids": report_ids,
                            "report_count": len(report_ids),
                            "last_seen_at": now,
                            "risk_level": self._max_risk(cluster.risk_level, report.risk_level),
                            "summary": (
                                f"{len(report_ids)} related SautiRelay reports in {region}. "
                                "Human verification is recommended."
                            ),
                            "confidence_score": max(cluster.confidence_score, report.confidence_score),
                            "updated_at": now,
                        }
                    )
                    await self._repository.put_cluster(updated_cluster)
                    await self._repository.put_report(
                        report.model_copy(update={"cluster_id": cluster.id, "updated_at": now})
                    )
                    return

        clusters = await self._repository.list_clusters()
        matching = [
            cluster
            for cluster in clusters
            if cluster.category == report.category
            and cluster.region == region
            and cluster.status in {ClusterStatus.new, ClusterStatus.pending_review, ClusterStatus.verified}
        ]
        if matching:
            cluster = matching[0]
            report_ids = list(dict.fromkeys([*cluster.report_ids, report.id]))
            updated_cluster = cluster.model_copy(
                update={
                    "report_ids": report_ids,
                    "report_count": len(report_ids),
                    "last_seen_at": now,
                    "risk_level": self._max_risk(cluster.risk_level, report.risk_level),
                    "summary": (
                        f"{len(report_ids)} related SautiRelay reports in {region}. Human verification is recommended."
                    ),
                    "updated_at": now,
                }
            )
            await self._repository.put_cluster(updated_cluster)
            await self._repository.put_report(report.model_copy(update={"cluster_id": cluster.id, "updated_at": now}))
            return
        cluster = SignalClusterDocument.model_validate(
            {
                "cluster_id": self._id("cluster"),
                "title": f"Possible {str(report.category).replace('_', ' ').title()}",
                "category": report.category,
                "region": region,
                "risk_level": report.risk_level,
                "summary": f"One SautiRelay report in {region}. Human verification is recommended.",
                "report_count": 1,
                "report_ids": [report.id],
                "first_seen_at": report.submitted_at,
                "last_seen_at": now,
                "confidence_score": report.confidence_score,
                "status": ClusterStatus.pending_review,
                "created_at": now,
                "updated_at": now,
            }
        )
        await self._repository.put_cluster(cluster)
        await self._repository.put_report(report.model_copy(update={"cluster_id": cluster.id, "updated_at": now}))

    def _apply_report_verification(self, report: ReportDocument, request: VerificationRequest) -> ReportDocument:
        status_by_decision = {
            VerificationDecision.verified: ReportStatus.verified,
            VerificationDecision.needs_more_info: ReportStatus.needs_more_info,
            VerificationDecision.duplicate: ReportStatus.duplicate,
            VerificationDecision.unverified_rumor: ReportStatus.unverified_rumor,
            VerificationDecision.dismissed: ReportStatus.dismissed,
            VerificationDecision.archive: ReportStatus.archived,
            VerificationDecision.archived: ReportStatus.archived,
            VerificationDecision.escalate_immediately: ReportStatus.verified,
        }
        return report.model_copy(
            update={
                "status": status_by_decision[request.decision],
                "category": request.adjusted_category or report.category,
                "risk_level": request.adjusted_risk_level or report.risk_level,
                "approximate_location": request.adjusted_location or report.approximate_location,
                "confidence_score": self._confidence_value(request.confidence)
                if request.confidence is not None
                else report.confidence_score,
                "updated_at": utc_now(),
            }
        )

    async def _create_escalation_from_report(
        self,
        report: ReportDocument,
        request: EscalationCreateRequest,
        actor: AuthenticatedUser,
    ) -> EscalationDocument:
        escalation = self._build_escalation(None, report, request)
        await self._repository.put_escalation(escalation)
        await self._repository.put_report(
            report.model_copy(update={"status": ReportStatus.escalated, "updated_at": utc_now()})
        )
        await self._audit(actor.id, "report.escalated", "report", report.id)
        return escalation

    async def _queue_escalation_from_report(
        self,
        report: ReportDocument,
        request: EscalationCreateRequest,
        actor: AuthenticatedUser,
    ) -> EscalationDocument:
        now = utc_now()
        escalation = EscalationDocument.model_validate(
            {
                "escalation_id": self._id("escalation"),
                "cluster_id": None,
                "report_id": report.id,
                "assigned_to": request.assigned_to,
                "assigned_organization": request.assigned_organization,
                "action_brief": "Mediator brief is being prepared. Please refresh shortly.",
                "safety_note": self._safe_mediator_note(request.safety_note),
                "urgency": request.urgency,
                "status": EscalationStatus.preparing_brief,
                "sent_at": now,
                "follow_up_due_at": request.follow_up_due_at,
                "created_at": now,
                "updated_at": now,
            }
        )
        await self._repository.put_escalation(escalation)
        await self._repository.put_report(
            report.model_copy(update={"status": ReportStatus.escalated, "updated_at": utc_now()})
        )
        await self._audit(actor.id, "report.escalation_queued", "report", report.id)
        return escalation

    async def finalize_report_escalation_brief(self, escalation_id: str, report_id: str, actor_id: str) -> None:
        try:
            report = await self._require_report(report_id)
            escalation = await self._require_escalation(escalation_id)
            request = EscalationCreateRequest.model_validate(
                {
                    "assigned_to": escalation.assigned_to,
                    "assigned_organization": escalation.assigned_organization,
                    "urgency": escalation.urgency,
                    "safety_note": escalation.safety_note,
                    "follow_up_due_at": escalation.follow_up_due_at,
                }
            )
            completed = self._build_escalation(None, report, request).model_copy(
                update={
                    "id": escalation.id,
                    "status": EscalationStatus.pending_acceptance,
                    "sent_at": escalation.sent_at,
                    "created_at": escalation.created_at,
                    "updated_at": utc_now(),
                }
            )
            await self._repository.put_escalation(completed)
            await self._audit(actor_id, "report.escalated", "report", report.id)
        except HTTPException as exc:
            await self._handle_background_escalation_failure(escalation_id, str(exc.detail), actor_id)
        except Exception as exc:  # pragma: no cover - defensive safety for background task failures
            await self._handle_background_escalation_failure(escalation_id, str(exc), actor_id)

    def _build_escalation(
        self,
        cluster: SignalClusterDocument | None,
        report: ReportDocument | None,
        request: EscalationCreateRequest,
    ) -> EscalationDocument:
        now = utc_now()
        source_summary = (
            cluster.summary
            if cluster is not None
            else report.summary
            if report is not None
            else "Verified SautiRelay signal."
        )
        area = (
            cluster.region
            if cluster is not None
            else self._region_from_location(report.approximate_location)
            if report is not None
            else "Approximate area only"
        )
        risk = (
            cluster.risk_level if cluster is not None else report.risk_level if report is not None else RiskLevel.medium
        )
        category = (
            cluster.category
            if cluster is not None
            else report.category
            if report is not None
            else ReportCategory.not_sure
        )
        try:
            ai_brief = OpenAIIntakeService().generate_mediator_brief(
                signal={
                    "category": category,
                    "risk_level": risk,
                    "summary": source_summary,
                    "area": area,
                    "urgency": request.urgency,
                },
                reports=[report] if report is not None else [],
                safety_note=request.safety_note,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

        recommended_items = ai_brief.recommended_response or [
            "Coordinate with trusted local peace actors.",
            "Record outcome and follow-up needs.",
        ]
        recommended = "\n".join(f"- {item}" for item in recommended_items)
        brief = (
            f"{ai_brief.title}\n\n"
            f"Risk: {ai_brief.risk_level}\n"
            f"Issue: {ai_brief.risk_type}\n"
            f"Area: {ai_brief.area}\n\n"
            f"Summary: {ai_brief.summary}\n\n"
            f"Suggested response:\n{recommended}\n\n"
            f"Follow-up: {ai_brief.follow_up_prompt}"
        )
        return EscalationDocument.model_validate(
            {
                "escalation_id": self._id("escalation"),
                "cluster_id": cluster.id if cluster is not None else None,
                "report_id": report.id if report is not None else None,
                "assigned_to": request.assigned_to,
                "assigned_organization": request.assigned_organization,
                "action_brief": brief,
                "safety_note": self._safe_mediator_note(request.safety_note),
                "urgency": request.urgency,
                "status": EscalationStatus.pending_acceptance,
                "sent_at": now,
                "follow_up_due_at": request.follow_up_due_at,
                "created_at": now,
                "updated_at": now,
            }
        )

    async def _mark_related_reports_resolved(self, escalation: EscalationDocument) -> None:
        if escalation.report_id is not None:
            report = await self._repository.get_report(escalation.report_id)
            if report is not None:
                await self._repository.put_report(
                    report.model_copy(update={"status": ReportStatus.resolved, "updated_at": utc_now()})
                )
        if escalation.cluster_id is not None:
            cluster = await self._repository.get_cluster(escalation.cluster_id)
            if cluster is not None:
                await self._repository.put_cluster(
                    cluster.model_copy(update={"status": ClusterStatus.resolved, "updated_at": utc_now()})
                )
                for report_id in cluster.report_ids:
                    report = await self._repository.get_report(report_id)
                    if report is not None:
                        await self._repository.put_report(
                            report.model_copy(update={"status": ReportStatus.resolved, "updated_at": utc_now()})
                        )

    @staticmethod
    def _confidence_value(confidence: float | str | None) -> float | None:
        if confidence is None:
            return None
        if isinstance(confidence, (int, float)):
            return float(confidence)
        return {"LOW": 0.35, "MEDIUM": 0.6, "HIGH": 0.85, "CRITICAL": 0.95}.get(confidence.upper(), 0.5)

    @staticmethod
    def _safe_mediator_note(note: str) -> str:
        _ = note
        return "Protect the source. Use approximate area only."

    @staticmethod
    def _max_risk(first: RiskLevel, second: RiskLevel) -> RiskLevel:
        rank = {RiskLevel.low: 0, RiskLevel.medium: 1, RiskLevel.high: 2, RiskLevel.critical: 3}
        return first if rank[first] >= rank[second] else second

    @staticmethod
    def _region_from_location(location: ApproximateLocation) -> str:
        return (
            location.admin_level_2
            or location.nearest_area
            or location.admin_level_1
            or location.country
            or "Approximate area only"
        )

    @staticmethod
    def _safe_status(status_value: ReportStatus | str) -> str:
        status_text = str(status_value)
        mapping = {
            ReportStatus.new.value: "Received",
            ReportStatus.processing.value: "Under review",
            ReportStatus.pending_review.value: "Under review",
            ReportStatus.needs_more_info.value: "Under review",
            ReportStatus.verified.value: "Verified",
            ReportStatus.escalated.value: "Escalated to trusted mediator",
            ReportStatus.resolved.value: "Closed",
            ReportStatus.duplicate.value: "Unable to verify",
            ReportStatus.unverified_rumor.value: "Unable to verify",
            ReportStatus.dismissed.value: "Unable to verify",
            ReportStatus.archived.value: "Closed",
        }
        return mapping.get(status_text, "Under review")

    async def _handle_background_report_failure(self, report_id: str, detail: str) -> None:
        self._logger.warning("Background report processing failed for %s: %s", report_id, detail)
        report = await self._repository.get_report(report_id)
        if report is None:
            return
        await self._repository.put_report(report.model_copy(update={"status": ReportStatus.new, "updated_at": utc_now()}))
        await self._audit(None, "report.ai_processing_failed", "report", report_id, {"detail": detail[:200]})

    async def _handle_background_escalation_failure(self, escalation_id: str, detail: str, actor_id: str) -> None:
        self._logger.warning("Background escalation brief generation failed for %s: %s", escalation_id, detail)
        escalation = await self._repository.get_escalation(escalation_id)
        if escalation is None:
            return
        failed = escalation.model_copy(
            update={
                "status": EscalationStatus.pending_acceptance,
                "action_brief": "Mediator brief could not be generated automatically. Please proceed with manual review.",
                "updated_at": utc_now(),
            }
        )
        await self._repository.put_escalation(failed)
        await self._audit(
            actor_id,
            "escalation.brief_generation_failed",
            "escalation",
            escalation_id,
            {"detail": detail[:200]},
        )

    async def _audit(
        self,
        actor_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        await self._repository.append_audit_log(
            AuditLogDocument.model_validate(
                {
                    "id": self._id("audit"),
                    "actor_id": actor_id,
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "metadata": metadata or {},
                    "created_at": utc_now(),
                }
            )
        )

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"

    @staticmethod
    def _tracking_code() -> str:
        return f"SR-{secrets.token_hex(3).upper()}"

    @staticmethod
    def _local_encrypted_placeholder(value: str) -> str:
        return f"local-encrypted::{value}"

    @staticmethod
    def _restore_local_placeholder(value: str) -> str:
        return value.removeprefix("local-encrypted::")


class WorkflowRules:
    """Small explicit workflow transition helper for tests and route services."""

    def can_escalate_report(self, status_value: str) -> bool:
        return status_value == ReportStatus.verified.value

    def can_transition_report(self, from_status: str, to_status: str) -> bool:
        allowed = {
            ReportStatus.new.value: {ReportStatus.processing.value, ReportStatus.pending_review.value},
            ReportStatus.processing.value: {ReportStatus.pending_review.value},
            ReportStatus.pending_review.value: {
                ReportStatus.verified.value,
                ReportStatus.needs_more_info.value,
                ReportStatus.duplicate.value,
                ReportStatus.unverified_rumor.value,
                ReportStatus.dismissed.value,
                ReportStatus.archived.value,
            },
            ReportStatus.verified.value: {ReportStatus.escalated.value, ReportStatus.resolved.value},
            ReportStatus.escalated.value: {ReportStatus.resolved.value},
        }
        return to_status in allowed.get(from_status, set())

    def can_transition_escalation(self, from_status: str, to_status: str) -> bool:
        allowed = {
            "ESCALATED": {EscalationStatus.accepted.value},
            EscalationStatus.preparing_brief.value: {EscalationStatus.pending_acceptance.value},
            EscalationStatus.pending_acceptance.value: {EscalationStatus.accepted.value},
            EscalationStatus.accepted.value: {
                EscalationStatus.action_recorded.value,
                EscalationStatus.follow_up_requested.value,
                EscalationStatus.resolved.value,
            },
            EscalationStatus.action_recorded.value: {
                EscalationStatus.follow_up_requested.value,
                EscalationStatus.resolved.value,
            },
        }
        return to_status in allowed.get(from_status, set())
