"""Optional in-memory demo fixtures for verifier, mediator, and analytics POC."""

from __future__ import annotations

import logging
from datetime import timedelta

from backend.app.core.config import Settings
from backend.app.core.models import (
    ApproximateLocation,
    AuthenticatedUser,
    ClusterStatus,
    EscalationDocument,
    EscalationStatus,
    OutcomeDocument,
    OutcomeType,
    ReportCategory,
    ReportDocument,
    ReportStatus,
    RiskLevel,
    SignalClusterDocument,
    Urgency,
    UserRole,
    utc_now,
)
from backend.app.repositories.memory import SautiRelayRepository
from backend.app.services.clustering import deterministic_embedding
from backend.app.services.workflow import WorkflowService

logger = logging.getLogger(__name__)

# Subset of demo reports to run through real AI when DEMO_SEED_WITH_AI=1 and OPENAI_API_KEY is set.
DEMO_AI_PROCESS_IDS: tuple[str, ...] = ("demo_report_new_water", "demo_report_new_aid")


def _loc(*, area: str, country: str = "Kenya", admin1: str = "Machakos") -> ApproximateLocation:
    return ApproximateLocation(
        country=country,
        admin_level_1=admin1,
        nearest_area=area,
        raw_location_text=f"{area} area",
        location_precision="COARSE",
    )


def _emb(text: str, *, dimensions: int) -> list[float]:
    return deterministic_embedding(text, dimensions=dimensions)


async def seed_demo_data(repository: SautiRelayRepository, *, embedding_dimensions: int = 96) -> None:
    now = utc_now()
    base = now - timedelta(days=1)

    reports: list[ReportDocument] = [
        ReportDocument(
            reportId="demo_report_new_water",
            trackingCode="SR-DEMO01",
            submitted_at=base,
            channel="pwa",
            language="en",
            raw_text_encrypted=(
                "local-encrypted::Rumors of tension at the Syokimau water point between herders and residents."
            ),
            redacted_text=None,
            translated_text=None,
            summary=None,
            approximate_location=_loc(area="Syokimau"),
            category=ReportCategory.water_or_resource_conflict,
            urgency=Urgency.within_24_hours,
            risk_level=RiskLevel.medium,
            confidence_score=0.0,
            status=ReportStatus.new,
            cluster_id=None,
            created_at=base,
            updated_at=base,
        ),
        ReportDocument(
            reportId="demo_report_new_aid",
            trackingCode="SR-DEMO02",
            submitted_at=base,
            channel="pwa",
            language="en",
            raw_text_encrypted=(
                "local-encrypted::Camp leaders asked for payment before food distribution in Goma north."
            ),
            redacted_text=None,
            translated_text=None,
            summary=None,
            approximate_location=_loc(area="Goma north", country="DRC", admin1="North Kivu"),
            category=ReportCategory.aid_diversion,
            urgency=Urgency.this_week,
            risk_level=RiskLevel.medium,
            confidence_score=0.0,
            status=ReportStatus.new,
            cluster_id=None,
            created_at=base,
            updated_at=base,
        ),
        ReportDocument(
            reportId="demo_report_pr_water_a",
            trackingCode="SR-DEMO03",
            submitted_at=base + timedelta(hours=1),
            channel="pwa",
            language="en",
            raw_text_encrypted=(
                "local-encrypted::Community members fear access to the borehole may be blocked after market day."
            ),
            redacted_text=("Community members fear access to the borehole may be blocked after market day."),
            translated_text=("Community members fear access to the borehole may be blocked after market day."),
            summary="Borehole access concern after market day in Syokimau.",
            approximate_location=_loc(area="Syokimau"),
            category=ReportCategory.water_or_resource_conflict,
            urgency=Urgency.this_week,
            risk_level=RiskLevel.high,
            confidence_score=0.78,
            status=ReportStatus.pending_review,
            cluster_id="demo_cluster_water_syokimau",
            embedding=_emb("water borehole syokimau market tension", dimensions=embedding_dimensions),
            needs_human_review=True,
            ai_recommended_mediator_action=(
                "Facilitate calm dialogue between herders and residents; avoid public blame."
            ),
            ai_safety_warnings=["Do not disclose reporter details.", "Use approximate location only."],
            created_at=base,
            updated_at=now,
        ),
        ReportDocument(
            reportId="demo_report_pr_water_b",
            trackingCode="SR-DEMO04",
            submitted_at=base + timedelta(hours=2),
            channel="pwa",
            language="en",
            raw_text_encrypted=(
                "local-encrypted::Youth gathering was reported near the same borehole area this evening."
            ),
            redacted_text=("Youth gathering was reported near the same borehole area this evening."),
            translated_text=("Youth gathering was reported near the same borehole area this evening."),
            summary="Evening gathering near Syokimau borehole.",
            approximate_location=_loc(area="Syokimau"),
            category=ReportCategory.water_or_resource_conflict,
            urgency=Urgency.within_24_hours,
            risk_level=RiskLevel.high,
            confidence_score=0.74,
            status=ReportStatus.pending_review,
            cluster_id="demo_cluster_water_syokimau",
            embedding=_emb("water borehole syokimau youth gathering evening", dimensions=embedding_dimensions),
            needs_human_review=True,
            ai_recommended_mediator_action="Offer neutral venue for community leaders to compare accounts.",
            ai_safety_warnings=["Do not disclose reporter details."],
            created_at=base,
            updated_at=now,
        ),
        ReportDocument(
            reportId="demo_report_verified_land",
            trackingCode="SR-DEMO05",
            submitted_at=base + timedelta(hours=3),
            channel="pwa",
            language="en",
            raw_text_encrypted=(
                "local-encrypted::Boundary dispute between two families over a small plot near the school."
            ),
            redacted_text=("Boundary dispute between two families over a small plot near the school."),
            translated_text=("Boundary dispute between two families over a small plot near the school."),
            summary="Land boundary dispute near school in Athi River.",
            approximate_location=_loc(area="Athi River", admin1="Machakos"),
            category=ReportCategory.land_conflict,
            urgency=Urgency.routine,
            risk_level=RiskLevel.medium,
            confidence_score=0.81,
            status=ReportStatus.verified,
            cluster_id="demo_cluster_land_verified",
            embedding=_emb("land boundary dispute school plot athi river", dimensions=embedding_dimensions),
            needs_human_review=False,
            ai_recommended_mediator_action="Map dispute with local elders; document agreed boundaries.",
            ai_safety_warnings=["Do not disclose reporter details."],
            created_at=base,
            updated_at=now,
        ),
        ReportDocument(
            reportId="demo_report_resolved_election",
            trackingCode="SR-DEMO06",
            submitted_at=base + timedelta(hours=4),
            channel="pwa",
            language="en",
            raw_text_encrypted="local-encrypted::Voters reported intimidation outside a polling station last week.",
            redacted_text="Voters reported intimidation outside a polling station last week.",
            translated_text="Voters reported intimidation outside a polling station last week.",
            summary="Past election intimidation report (closed).",
            approximate_location=_loc(area="Nairobi East", admin1="Nairobi"),
            category=ReportCategory.election_intimidation,
            urgency=Urgency.routine,
            risk_level=RiskLevel.low,
            confidence_score=0.66,
            status=ReportStatus.resolved,
            cluster_id="demo_cluster_election_archived",
            embedding=_emb("election intimidation polling station nairobi", dimensions=embedding_dimensions),
            needs_human_review=False,
            ai_recommended_mediator_action="Document with electoral board liaison if recurrence is reported.",
            ai_safety_warnings=["Do not disclose reporter details."],
            created_at=base,
            updated_at=now,
        ),
        ReportDocument(
            reportId="demo_report_needs_info_gbv",
            trackingCode="SR-DEMO07",
            submitted_at=base + timedelta(hours=5),
            channel="pwa",
            language="en",
            raw_text_encrypted="local-encrypted::Women near the transit site said protection patrols stopped.",
            redacted_text="Women near the transit site said protection patrols stopped.",
            translated_text="Women near the transit site said protection patrols stopped.",
            summary="Protection concern near transit site needs verifier follow-up.",
            approximate_location=_loc(area="Transit site", country="South Sudan", admin1="Upper Nile"),
            category=ReportCategory.gbv_or_protection_risk,
            urgency=Urgency.today,
            risk_level=RiskLevel.high,
            confidence_score=0.69,
            status=ReportStatus.needs_more_info,
            cluster_id=None,
            embedding=_emb("protection patrols women transit site upper nile", dimensions=embedding_dimensions),
            needs_human_review=True,
            ai_recommended_mediator_action="Do not escalate until a protection-safe verification path is confirmed.",
            ai_safety_warnings=[
                "Do not disclose reporter details.",
                "Use protection referral pathways if the report is verified.",
            ],
            created_at=base,
            updated_at=now,
        ),
        ReportDocument(
            reportId="demo_report_unverified_rumor",
            trackingCode="SR-DEMO08",
            submitted_at=base + timedelta(hours=6),
            channel="pwa",
            language="en",
            raw_text_encrypted="local-encrypted::People online claimed an armed group entered the town.",
            redacted_text="People online claimed an armed group entered the town.",
            translated_text="People online claimed an armed group entered the town.",
            summary="Online armed-group claim marked as unverified rumor.",
            approximate_location=_loc(area="Garissa outskirts", admin1="Garissa"),
            category=ReportCategory.community_rumor,
            urgency=Urgency.today,
            risk_level=RiskLevel.medium,
            confidence_score=0.41,
            status=ReportStatus.unverified_rumor,
            cluster_id=None,
            embedding=_emb("online rumor armed group town garissa", dimensions=embedding_dimensions),
            needs_human_review=False,
            ai_recommended_mediator_action="No mediator action unless corroborated by trusted local sources.",
            ai_safety_warnings=["Avoid amplifying unverified armed-group claims."],
            created_at=base,
            updated_at=now,
        ),
    ]

    clusters: list[SignalClusterDocument] = [
        SignalClusterDocument(
            clusterId="demo_cluster_water_syokimau",
            title="Possible Water Or Resource Conflict",
            category=ReportCategory.water_or_resource_conflict,
            region="Syokimau",
            risk_level=RiskLevel.high,
            summary="Two SautiRelay reports in Syokimau. Human verification is recommended.",
            report_count=2,
            report_ids=["demo_report_pr_water_a", "demo_report_pr_water_b"],
            first_seen_at=base,
            last_seen_at=now,
            confidence_score=0.76,
            status=ClusterStatus.pending_review,
            created_at=base,
            updated_at=now,
        ),
        SignalClusterDocument(
            clusterId="demo_cluster_land_verified",
            title="Possible Land Conflict",
            category=ReportCategory.land_conflict,
            region="Athi River",
            risk_level=RiskLevel.medium,
            summary="Verified land signal in Athi River awaiting optional escalation.",
            report_count=1,
            report_ids=["demo_report_verified_land"],
            first_seen_at=base,
            last_seen_at=now,
            confidence_score=0.81,
            status=ClusterStatus.verified,
            created_at=base,
            updated_at=now,
        ),
        SignalClusterDocument(
            clusterId="demo_cluster_election_archived",
            title="Possible Election Intimidation",
            category=ReportCategory.election_intimidation,
            region="Nairobi East",
            risk_level=RiskLevel.low,
            summary="Historical election signal (resolved).",
            report_count=1,
            report_ids=["demo_report_resolved_election"],
            first_seen_at=base,
            last_seen_at=now,
            confidence_score=0.66,
            status=ClusterStatus.resolved,
            created_at=base,
            updated_at=now,
        ),
    ]

    follow = now + timedelta(days=3)
    escalations: list[EscalationDocument] = [
        EscalationDocument(
            escalationId="demo_escalation_pending",
            cluster_id="demo_cluster_land_verified",
            report_id=None,
            assigned_to="mediator@sautirelay.dev",
            assigned_organization="Local mediation network",
            action_brief=(
                "SautiRelay mediator brief\n\nRisk: MEDIUM\nIssue: LAND_CONFLICT\nArea: Athi River\n\n"
                "Summary: Boundary dispute between two families over a small plot near the school.\n\n"
                "Suggested response: Verify safely with trusted local peace actors and avoid public accusation."
            ),
            safety_note="Protect the source. Use approximate area only.",
            urgency=Urgency.within_24_hours,
            status=EscalationStatus.pending_acceptance,
            sent_at=base + timedelta(hours=5),
            follow_up_due_at=follow,
            created_at=base + timedelta(hours=5),
            updated_at=base + timedelta(hours=5),
        ),
        EscalationDocument(
            escalationId="demo_escalation_accepted",
            cluster_id=None,
            report_id="demo_report_resolved_election",
            assigned_to="mediator@sautirelay.dev",
            assigned_organization="Local mediation network",
            action_brief="Historical demo escalation tied to resolved election signal.",
            safety_note="Protect the source. Use approximate area only.",
            urgency=Urgency.routine,
            status=EscalationStatus.accepted,
            sent_at=base + timedelta(hours=6),
            accepted_at=base + timedelta(hours=7),
            follow_up_due_at=follow,
            created_at=base + timedelta(hours=6),
            updated_at=base + timedelta(hours=7),
        ),
    ]

    outcomes: list[OutcomeDocument] = [
        OutcomeDocument(
            outcomeId="demo_outcome_1",
            escalation_id="demo_escalation_accepted",
            outcome_type=OutcomeType.dialogue_held,
            notes="Demo outcome: community forum completed.",
            deescalated=True,
            follow_up_required=False,
            recorded_by="user_mediator_local",
            created_at=base + timedelta(hours=8),
        ),
    ]

    for report in reports:
        await repository.put_report(report)
    for cluster in clusters:
        await repository.put_cluster(cluster)
    for escalation in escalations:
        await repository.put_escalation(escalation)
    for outcome in outcomes:
        await repository.put_outcome(outcome)


async def run_demo_seed(
    repository: SautiRelayRepository,
    workflow: WorkflowService,
    settings: Settings,
) -> None:
    await seed_demo_data(repository, embedding_dimensions=settings.embedding_dimensions or 96)
    if not settings.demo_seed_with_ai or not settings.openai_api_key:
        return
    verifier = AuthenticatedUser(
        id="user_verifier_local",
        username=settings.verifier_username,
        role=UserRole.verifier,
        organization_id="org_local_peace_committee",
    )
    for report_id in DEMO_AI_PROCESS_IDS:
        try:
            await workflow.process_report(report_id, verifier)
        except Exception:
            logger.exception("Demo seed AI hydration failed for report %s", report_id)
