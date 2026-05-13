from collections import Counter
from copy import deepcopy
from typing import Protocol

from backend.app.core.models import (
    AuditLogDocument,
    DashboardMetrics,
    EscalationDocument,
    MetricCount,
    OutcomeDocument,
    ReportCategory,
    ReportDocument,
    ReportStatus,
    RiskLevel,
    SignalClusterDocument,
    VerificationDocument,
)


class SautiRelayRepository(Protocol):
    async def put_report(self, report: ReportDocument) -> ReportDocument: ...
    async def get_report(self, report_id: str) -> ReportDocument | None: ...
    async def get_report_by_tracking_code(self, tracking_code: str) -> ReportDocument | None: ...
    async def list_reports(self, status: ReportStatus | None = None) -> list[ReportDocument]: ...
    async def put_cluster(self, cluster: SignalClusterDocument) -> SignalClusterDocument: ...
    async def get_cluster(self, cluster_id: str) -> SignalClusterDocument | None: ...
    async def list_clusters(self) -> list[SignalClusterDocument]: ...
    async def put_verification(self, verification: VerificationDocument) -> VerificationDocument: ...
    async def put_escalation(self, escalation: EscalationDocument) -> EscalationDocument: ...
    async def get_escalation(self, escalation_id: str) -> EscalationDocument | None: ...
    async def list_escalations(self, assigned_to: str | None = None) -> list[EscalationDocument]: ...
    async def put_outcome(self, outcome: OutcomeDocument) -> OutcomeDocument: ...
    async def list_outcomes(self) -> list[OutcomeDocument]: ...
    async def append_audit_log(self, event: AuditLogDocument) -> AuditLogDocument: ...
    async def dashboard_metrics(self) -> DashboardMetrics: ...


class InMemorySautiRelayRepository:
    """DynamoDB-shaped document repository for local development."""

    def __init__(self) -> None:
        self._reports: dict[str, ReportDocument] = {}
        self._tracking_index: dict[str, str] = {}
        self._clusters: dict[str, SignalClusterDocument] = {}
        self._verifications: dict[str, VerificationDocument] = {}
        self._escalations: dict[str, EscalationDocument] = {}
        self._outcomes: dict[str, OutcomeDocument] = {}
        self._audit_logs: dict[str, AuditLogDocument] = {}

    async def put_report(self, report: ReportDocument) -> ReportDocument:
        stored = deepcopy(report)
        self._reports[stored.id] = stored
        self._tracking_index[stored.public_tracking_code] = stored.id
        return deepcopy(stored)

    async def get_report(self, report_id: str) -> ReportDocument | None:
        report = self._reports.get(report_id)
        return deepcopy(report) if report is not None else None

    async def get_report_by_tracking_code(self, tracking_code: str) -> ReportDocument | None:
        report_id = self._tracking_index.get(tracking_code)
        if report_id is None:
            return None
        return await self.get_report(report_id)

    async def list_reports(self, status: ReportStatus | None = None) -> list[ReportDocument]:
        reports = list(self._reports.values())
        if status is not None:
            reports = [report for report in reports if report.status == status]
        return deepcopy(reports)

    async def put_cluster(self, cluster: SignalClusterDocument) -> SignalClusterDocument:
        stored = deepcopy(cluster)
        self._clusters[stored.id] = stored
        return deepcopy(stored)

    async def get_cluster(self, cluster_id: str) -> SignalClusterDocument | None:
        cluster = self._clusters.get(cluster_id)
        return deepcopy(cluster) if cluster is not None else None

    async def list_clusters(self) -> list[SignalClusterDocument]:
        return deepcopy(list(self._clusters.values()))

    async def put_verification(self, verification: VerificationDocument) -> VerificationDocument:
        stored = deepcopy(verification)
        self._verifications[stored.id] = stored
        return deepcopy(stored)

    async def put_escalation(self, escalation: EscalationDocument) -> EscalationDocument:
        stored = deepcopy(escalation)
        self._escalations[stored.id] = stored
        return deepcopy(stored)

    async def get_escalation(self, escalation_id: str) -> EscalationDocument | None:
        escalation = self._escalations.get(escalation_id)
        return deepcopy(escalation) if escalation is not None else None

    async def list_escalations(self, assigned_to: str | None = None) -> list[EscalationDocument]:
        escalations = list(self._escalations.values())
        if assigned_to is not None:
            escalations = [item for item in escalations if item.assigned_to == assigned_to]
        return deepcopy(escalations)

    async def put_outcome(self, outcome: OutcomeDocument) -> OutcomeDocument:
        stored = deepcopy(outcome)
        self._outcomes[stored.id] = stored
        return deepcopy(stored)

    async def list_outcomes(self) -> list[OutcomeDocument]:
        return deepcopy(list(self._outcomes.values()))

    async def append_audit_log(self, event: AuditLogDocument) -> AuditLogDocument:
        stored = deepcopy(event)
        self._audit_logs[stored.id] = stored
        return deepcopy(stored)

    async def dashboard_metrics(self) -> DashboardMetrics:
        status_counts = Counter(str(report.status) for report in self._reports.values())
        category_counts = Counter(str(report.category) for report in self._reports.values())
        risk_counts = Counter(str(report.risk_level) for report in self._reports.values())
        high_risk = sum(1 for report in self._reports.values() if str(report.risk_level) in {"HIGH", "CRITICAL"})
        active_clusters = sum(
            1 for cluster in self._clusters.values() if str(cluster.status) not in {"RESOLVED", "ARCHIVED"}
        )
        escalated_signals = sum(1 for report in self._reports.values() if str(report.status) == "ESCALATED")
        resolved_signals = sum(1 for report in self._reports.values() if str(report.status) == "RESOLVED")
        return DashboardMetrics(
            total_reports=len(self._reports),
            reports_by_status=dict(status_counts),
            reports_by_category=[
                MetricCount(label=category.value, count=category_counts.get(category.value, 0))
                for category in ReportCategory
                if category_counts.get(category.value, 0) > 0
            ],
            risk_levels=[
                MetricCount(label=risk.value, count=risk_counts.get(risk.value, 0))
                for risk in RiskLevel
                if risk_counts.get(risk.value, 0) > 0
            ],
            active_clusters=active_clusters,
            escalated_signals=escalated_signals,
            resolved_signals=resolved_signals,
            clusters_total=len(self._clusters),
            escalations_total=len(self._escalations),
            outcomes_total=len(self._outcomes),
            high_risk_reports=high_risk,
        )
