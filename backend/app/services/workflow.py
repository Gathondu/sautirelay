import re
import secrets
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status

from backend.app.core.models import (
    ApproximateLocation,
    AuditLogDocument,
    AuthenticatedUser,
    ClusterStatus,
    DashboardMetrics,
    EscalationCreateRequest,
    EscalationDocument,
    EscalationStatus,
    IntakeResult,
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
    Urgency,
    VerificationDecision,
    VerificationDocument,
    VerificationRequest,
    utc_now,
)
from backend.app.repositories.memory import SautiRelayRepository


class WorkflowService:
    def __init__(self, repository: SautiRelayRepository) -> None:
        self._repository = repository

    async def submit_report(self, request: ReportCreateRequest) -> ReportCreateResponse:
        now = utc_now()
        report = ReportDocument(
            id=self._id("report"),
            public_tracking_code=self._tracking_code(),
            submitted_at=now,
            channel=request.channel,
            language=request.language,
            raw_text_encrypted=self._local_encrypted_placeholder(request.text),
            redacted_text=None,
            translated_text=None,
            summary=None,
            approximate_location=request.location,
            raw_location_encrypted=self._local_encrypted_placeholder(request.location.model_dump_json()),
            location_precision=request.location.location_precision,
            category=request.category_hint,
            urgency=request.timeframe,
            risk_level=RiskLevel.high if request.immediate_danger else RiskLevel.medium,
            confidence_score=0.0,
            reporter_anonymous=True,
            status=ReportStatus.new,
            created_at=now,
            updated_at=now,
        )
        await self._repository.put_report(report)
        await self._attach_to_cluster(report)
        report = await self._require_report(report.id)
        await self._audit(None, "report.submitted", "report", report.id)
        return ReportCreateResponse(
            report_id=report.id,
            tracking_code=report.public_tracking_code,
            status=report.status,
            safe_status=self._safe_status(report.status),
            message="Your report has been received safely.",
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
        now = utc_now()
        processing_report = report.model_copy(update={"status": ReportStatus.processing, "updated_at": now})
        await self._repository.put_report(processing_report)
        intake = self._fallback_intake(processing_report)
        updated_report = processing_report.model_copy(
            update={
                "redacted_text": intake.redacted_text,
                "translated_text": intake.translated_text,
                "summary": intake.summary,
                "category": intake.category,
                "urgency": intake.urgency,
                "risk_level": intake.risk_level,
                "confidence_score": intake.confidence_score,
                "status": ReportStatus.pending_review,
                "updated_at": utc_now(),
            }
        )
        await self._repository.put_report(updated_report)
        await self._attach_to_cluster(updated_report)
        await self._audit(actor.id, "report.processed", "report", report_id)
        return await self._require_report(report_id)

    async def verify_report(
        self,
        report_id: str,
        request: VerificationRequest,
        actor: AuthenticatedUser,
    ) -> ReportDocument | EscalationDocument:
        report = await self._require_report(report_id)
        verification = VerificationDocument(
            id=self._id("verification"),
            report_id=report.id,
            cluster_id=None,
            verifier_id=actor.id,
            decision=request.decision,
            notes=request.notes,
            confidence=self._confidence_value(request.confidence),
            adjusted_category=request.adjusted_category,
            adjusted_risk_level=request.adjusted_risk_level,
            adjusted_location=request.adjusted_location,
            created_at=utc_now(),
        )
        await self._repository.put_verification(verification)
        updated_report = self._apply_report_verification(report, request)
        await self._repository.put_report(updated_report)
        await self._audit(actor.id, "report.verified", "report", report.id, {"decision": str(request.decision)})
        if request.decision == VerificationDecision.escalate_immediately:
            escalation_request = EscalationCreateRequest()
            return await self._create_escalation_from_report(updated_report, escalation_request, actor)
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
        verification = VerificationDocument(
            id=self._id("verification"),
            report_id=None,
            cluster_id=cluster.id,
            verifier_id=actor.id,
            decision=request.decision,
            notes=request.notes,
            confidence=self._confidence_value(request.confidence),
            adjusted_category=request.adjusted_category,
            adjusted_risk_level=request.adjusted_risk_level,
            adjusted_location=request.adjusted_location,
            created_at=utc_now(),
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
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cluster must be verified before escalation")
        escalation = self._build_escalation(cluster, None, request)
        updated_cluster = cluster.model_copy(update={"status": ClusterStatus.escalated, "updated_at": utc_now()})
        await self._repository.put_cluster(updated_cluster)
        await self._repository.put_escalation(escalation)
        await self._audit(actor.id, "cluster.escalated", "cluster", cluster.id)
        return escalation

    async def list_escalations(self, actor: AuthenticatedUser) -> list[EscalationDocument]:
        escalations = await self._repository.list_escalations()
        return [item for item in escalations if item.assigned_to in {actor.username, actor.id, "mediator-local-1"}]

    async def get_escalation(self, escalation_id: str, actor: AuthenticatedUser) -> EscalationDocument:
        escalation = await self._require_escalation(escalation_id)
        if escalation.assigned_to not in {actor.username, actor.id, "mediator-local-1"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Escalation is assigned to another mediator")
        return escalation

    async def accept_escalation(self, escalation_id: str, actor: AuthenticatedUser) -> EscalationDocument:
        escalation = await self.get_escalation(escalation_id, actor)
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
        outcome = OutcomeDocument(
            id=self._id("outcome"),
            escalation_id=escalation.id,
            outcome_type=request.outcome_type,
            notes=request.notes,
            deescalated=request.deescalated,
            follow_up_required=request.follow_up_required,
            recorded_by=actor.id,
            created_at=now,
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

    async def _attach_to_cluster(self, report: ReportDocument) -> None:
        region = self._region_from_location(report.approximate_location)
        clusters = await self._repository.list_clusters()
        matching = [
            cluster
            for cluster in clusters
            if cluster.category == report.category
            and cluster.region == region
            and cluster.status in {ClusterStatus.new, ClusterStatus.pending_review, ClusterStatus.verified}
        ]
        now = utc_now()
        if matching:
            cluster = matching[0]
            report_ids = list(dict.fromkeys([*cluster.report_ids, report.id]))
            updated_cluster = cluster.model_copy(
                update={
                    "report_ids": report_ids,
                    "report_count": len(report_ids),
                    "last_seen_at": now,
                    "risk_level": self._max_risk(cluster.risk_level, report.risk_level),
                    "summary": f"{len(report_ids)} related SautiRelay reports in {region}. Human verification is recommended.",
                    "updated_at": now,
                }
            )
            await self._repository.put_cluster(updated_cluster)
            await self._repository.put_report(report.model_copy(update={"cluster_id": cluster.id, "updated_at": now}))
            return
        cluster = SignalClusterDocument(
            id=self._id("cluster"),
            title=f"Possible {str(report.category).replace('_', ' ').title()}",
            category=report.category,
            region=region,
            risk_level=report.risk_level,
            summary=f"One SautiRelay report in {region}. Human verification is recommended.",
            report_count=1,
            report_ids=[report.id],
            first_seen_at=report.submitted_at,
            last_seen_at=now,
            confidence_score=report.confidence_score,
            status=ClusterStatus.pending_review,
            created_at=now,
            updated_at=now,
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
        await self._repository.put_report(report.model_copy(update={"status": ReportStatus.escalated, "updated_at": utc_now()}))
        await self._audit(actor.id, "report.escalated", "report", report.id)
        return escalation

    def _build_escalation(
        self,
        cluster: SignalClusterDocument | None,
        report: ReportDocument | None,
        request: EscalationCreateRequest,
    ) -> EscalationDocument:
        now = utc_now()
        source_summary = cluster.summary if cluster is not None else report.summary if report is not None else "Verified SautiRelay signal."
        area = cluster.region if cluster is not None else self._region_from_location(report.approximate_location) if report is not None else "Approximate area only"
        risk = cluster.risk_level if cluster is not None else report.risk_level if report is not None else RiskLevel.medium
        category = cluster.category if cluster is not None else report.category if report is not None else ReportCategory.not_sure
        brief = (
            "SautiRelay mediator brief\n\n"
            f"Risk: {str(risk)}\n"
            f"Issue: {str(category)}\n"
            f"Area: {area}\n\n"
            f"Summary: {source_summary}\n\n"
            "Suggested response: Verify safely with trusted local peace actors and avoid public accusation."
        )
        return EscalationDocument(
            id=self._id("escalation"),
            cluster_id=cluster.id if cluster is not None else None,
            report_id=report.id if report is not None else None,
            assigned_to=request.assigned_to,
            assigned_organization=request.assigned_organization,
            action_brief=brief,
            safety_note=self._safe_mediator_note(request.safety_note),
            urgency=request.urgency,
            status=EscalationStatus.pending_acceptance,
            sent_at=now,
            follow_up_due_at=request.follow_up_due_at,
            created_at=now,
            updated_at=now,
        )

    async def _mark_related_reports_resolved(self, escalation: EscalationDocument) -> None:
        if escalation.report_id is not None:
            report = await self._repository.get_report(escalation.report_id)
            if report is not None:
                await self._repository.put_report(report.model_copy(update={"status": ReportStatus.resolved, "updated_at": utc_now()}))
        if escalation.cluster_id is not None:
            cluster = await self._repository.get_cluster(escalation.cluster_id)
            if cluster is not None:
                await self._repository.put_cluster(cluster.model_copy(update={"status": ClusterStatus.resolved, "updated_at": utc_now()}))
                for report_id in cluster.report_ids:
                    report = await self._repository.get_report(report_id)
                    if report is not None:
                        await self._repository.put_report(report.model_copy(update={"status": ReportStatus.resolved, "updated_at": utc_now()}))

    def _fallback_intake(self, report: ReportDocument) -> IntakeResult:
        raw_text = self._restore_local_placeholder(report.raw_text_encrypted)
        redacted = self._redact(raw_text)
        category = self._category_from_text(raw_text, report.category)
        urgency = self._urgency_from_text(raw_text, report.urgency)
        risk = self._risk_from_text(raw_text, urgency)
        summary = redacted[:240]
        return IntakeResult(
            category=category,
            urgency=urgency,
            risk_level=risk,
            confidence_score=0.64,
            redacted_text=redacted,
            translated_text=redacted,
            summary=summary,
            recommended_mediator_action="Review with trusted local mediators before any public action.",
            safety_warning="Do not disclose reporter details.",
            embedding=[],
        )

    @staticmethod
    def _redact(text: str) -> str:
        redacted = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", text)
        redacted = re.sub(r"\+?\d[\d\s().-]{7,}\d", "[PHONE]", redacted)
        redacted = re.sub(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", "[PERSON]", redacted)
        return redacted

    @staticmethod
    def _category_from_text(text: str, fallback: ReportCategory) -> ReportCategory:
        lowered = text.lower()
        if "water" in lowered or "borehole" in lowered or "herder" in lowered:
            return ReportCategory.water_or_resource_conflict
        if "aid" in lowered or "distribution" in lowered:
            return ReportCategory.aid_diversion
        if "election" in lowered or "poll" in lowered:
            return ReportCategory.election_intimidation
        if "hate" in lowered or "chased away" in lowered:
            return ReportCategory.hate_speech_or_incitement
        if "displacement" in lowered or "families are leaving" in lowered:
            return ReportCategory.displacement_risk
        return fallback

    @staticmethod
    def _urgency_from_text(text: str, fallback: Urgency) -> Urgency:
        lowered = text.lower()
        if "now" in lowered or "immediate" in lowered:
            return Urgency.now
        if "tomorrow" in lowered or "24 hour" in lowered:
            return Urgency.within_24_hours
        if "today" in lowered:
            return Urgency.today
        return fallback

    @staticmethod
    def _risk_from_text(text: str, urgency: Urgency) -> RiskLevel:
        lowered = text.lower()
        if "attack" in lowered or "armed" in lowered or urgency in {Urgency.now, Urgency.within_24_hours}:
            return RiskLevel.high
        if "rumor" in lowered or "blocked" in lowered:
            return RiskLevel.medium
        return RiskLevel.low

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
        return location.admin_level_2 or location.nearest_area or location.admin_level_1 or location.country or "Approximate area only"

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

    async def _audit(
        self,
        actor_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        await self._repository.append_audit_log(
            AuditLogDocument(
                id=self._id("audit"),
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                metadata=metadata or {},
                created_at=utc_now(),
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
