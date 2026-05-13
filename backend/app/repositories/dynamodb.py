from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any

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
from backend.app.services.s3_vectors import S3VectorStore


class DynamoDbSautiRelayRepository:
    """Single-table DynamoDB repository with S3 Vectors-backed report embeddings."""

    def __init__(
        self,
        *,
        table_name: str | None = None,
        region_name: str | None = None,
        table: object | None = None,
        vector_store: S3VectorStore | None = None,
    ) -> None:
        if table is None:
            if not table_name:
                raise RuntimeError("DYNAMODB_TABLE_NAME is required when REPOSITORY_BACKEND=dynamodb.")
            import boto3

            table = boto3.resource("dynamodb", region_name=region_name).Table(table_name)
        self._table = table
        self._vector_store = vector_store

    async def put_report(self, report: ReportDocument) -> ReportDocument:
        if self._vector_store is not None and report.embedding:
            self._vector_store.put_report_embedding(
                report_id=report.id,
                embedding=report.embedding,
                metadata={
                    "entityType": "REPORT",
                    "category": str(report.category),
                    "riskLevel": str(report.risk_level),
                    "status": str(report.status),
                },
            )

        document = report.model_dump(mode="json", by_alias=True)
        document.pop("embedding", None)
        self._put_item(
            entity_type="REPORT",
            entity_id=report.id,
            document=document,
            extra={
                "trackingCode": report.public_tracking_code,
                "status": str(report.status),
                "GSI1PK": f"TRACKING#{report.public_tracking_code}",
                "GSI1SK": f"REPORT#{report.id}",
                "GSI2PK": f"REPORT_STATUS#{report.status}",
                "GSI2SK": report.submitted_at.isoformat(),
            },
        )
        return await self.get_report(report.id) or report

    async def get_report(self, report_id: str) -> ReportDocument | None:
        item = self._get_item("REPORT", report_id)
        return self._report_from_item(item) if item is not None else None

    async def get_report_by_tracking_code(self, tracking_code: str) -> ReportDocument | None:
        items = self._query(
            index_name="GSI1",
            key_condition_expression="GSI1PK = :tracking_pk",
            expression_attribute_values={":tracking_pk": f"TRACKING#{tracking_code}"},
            limit=1,
        )
        if items:
            return self._report_from_item(items[0])
        return None

    async def list_reports(self, status: ReportStatus | None = None) -> list[ReportDocument]:
        reports = [self._report_from_item(item) for item in self._scan_entity("REPORT")]
        reports = [report for report in reports if report is not None]
        if status is not None:
            reports = [report for report in reports if report.status == status]
        return reports

    async def put_cluster(self, cluster: SignalClusterDocument) -> SignalClusterDocument:
        self._put_item(
            entity_type="CLUSTER",
            entity_id=cluster.id,
            document=cluster.model_dump(mode="json", by_alias=True),
            extra={
                "status": str(cluster.status),
                "GSI1PK": f"CLUSTER_STATUS#{cluster.status}",
                "GSI1SK": cluster.updated_at.isoformat(),
            },
        )
        return cluster

    async def delete_cluster(self, cluster_id: str) -> None:
        self._table.delete_item(Key=self._key("CLUSTER", cluster_id))

    async def get_cluster(self, cluster_id: str) -> SignalClusterDocument | None:
        item = self._get_item("CLUSTER", cluster_id)
        return self._model_from_item(SignalClusterDocument, item)

    async def list_clusters(self) -> list[SignalClusterDocument]:
        return [
            cluster
            for cluster in (self._model_from_item(SignalClusterDocument, item) for item in self._scan_entity("CLUSTER"))
            if cluster is not None
        ]

    async def put_verification(self, verification: VerificationDocument) -> VerificationDocument:
        self._put_item(
            entity_type="VERIFICATION",
            entity_id=verification.id,
            document=verification.model_dump(mode="json", by_alias=True),
        )
        return verification

    async def put_escalation(self, escalation: EscalationDocument) -> EscalationDocument:
        self._put_item(
            entity_type="ESCALATION",
            entity_id=escalation.id,
            document=escalation.model_dump(mode="json", by_alias=True),
            extra={
                "assignedTo": escalation.assigned_to,
                "status": str(escalation.status),
                "GSI1PK": f"ASSIGNED#{escalation.assigned_to}",
                "GSI1SK": escalation.sent_at.isoformat(),
            },
        )
        return escalation

    async def get_escalation(self, escalation_id: str) -> EscalationDocument | None:
        item = self._get_item("ESCALATION", escalation_id)
        return self._model_from_item(EscalationDocument, item)

    async def list_escalations(self, assigned_to: str | None = None) -> list[EscalationDocument]:
        escalations = [
            escalation
            for escalation in (
                self._model_from_item(EscalationDocument, item) for item in self._scan_entity("ESCALATION")
            )
            if escalation is not None
        ]
        if assigned_to is not None:
            escalations = [item for item in escalations if item.assigned_to == assigned_to]
        return escalations

    async def put_outcome(self, outcome: OutcomeDocument) -> OutcomeDocument:
        self._put_item(
            entity_type="OUTCOME",
            entity_id=outcome.id,
            document=outcome.model_dump(mode="json", by_alias=True),
        )
        return outcome

    async def list_outcomes(self) -> list[OutcomeDocument]:
        return [
            outcome
            for outcome in (self._model_from_item(OutcomeDocument, item) for item in self._scan_entity("OUTCOME"))
            if outcome is not None
        ]

    async def append_audit_log(self, event: AuditLogDocument) -> AuditLogDocument:
        self._put_item(
            entity_type="AUDIT",
            entity_id=event.id,
            document=event.model_dump(mode="json", by_alias=True),
        )
        return event

    async def dashboard_metrics(self) -> DashboardMetrics:
        reports = await self.list_reports()
        clusters = await self.list_clusters()
        escalations = await self.list_escalations()
        outcomes = await self.list_outcomes()
        status_counts = Counter(str(report.status) for report in reports)
        category_counts = Counter(str(report.category) for report in reports)
        risk_counts = Counter(str(report.risk_level) for report in reports)
        active_clusters = sum(1 for cluster in clusters if str(cluster.status) not in {"RESOLVED", "ARCHIVED"})
        high_risk = sum(1 for report in reports if str(report.risk_level) in {"HIGH", "CRITICAL"})
        return DashboardMetrics(
            total_reports=len(reports),
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
            escalated_signals=sum(1 for report in reports if str(report.status) == "ESCALATED"),
            resolved_signals=sum(1 for report in reports if str(report.status) == "RESOLVED"),
            clusters_total=len(clusters),
            escalations_total=len(escalations),
            outcomes_total=len(outcomes),
            high_risk_reports=high_risk,
        )

    def _put_item(
        self,
        *,
        entity_type: str,
        entity_id: str,
        document: dict[str, Any],
        extra: dict[str, Any] | None = None,
    ) -> None:
        item = {
            **self._key(entity_type, entity_id),
            "entityType": entity_type,
            "entityId": entity_id,
            "document": document,
            **(extra or {}),
        }
        self._table.put_item(Item=_to_dynamodb_value(item))

    def _get_item(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        response = self._table.get_item(Key=self._key(entity_type, entity_id))
        item = response.get("Item")
        return _from_dynamodb_value(item) if item else None

    def _scan_entity(self, entity_type: str) -> list[dict[str, Any]]:
        return self._scan(
            filter_expression="entityType = :entity_type",
            expression_attribute_values={":entity_type": entity_type},
        )

    def _scan(
        self,
        *,
        filter_expression: str | None = None,
        expression_attribute_values: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {}
        if filter_expression is not None:
            kwargs["FilterExpression"] = filter_expression
        if expression_attribute_values is not None:
            kwargs["ExpressionAttributeValues"] = _to_dynamodb_value(expression_attribute_values)

        items: list[dict[str, Any]] = []
        while True:
            response = self._table.scan(**kwargs)
            items.extend(_from_dynamodb_value(item) for item in response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return items
            kwargs["ExclusiveStartKey"] = last_key

    def _query(
        self,
        *,
        index_name: str,
        key_condition_expression: str,
        expression_attribute_values: dict[str, Any],
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {
            "IndexName": index_name,
            "KeyConditionExpression": key_condition_expression,
            "ExpressionAttributeValues": _to_dynamodb_value(expression_attribute_values),
        }
        if limit is not None:
            kwargs["Limit"] = limit
        response = self._table.query(**kwargs)
        return [_from_dynamodb_value(item) for item in response.get("Items", [])]

    def _report_from_item(self, item: dict[str, Any] | None) -> ReportDocument | None:
        report = self._model_from_item(ReportDocument, item)
        if report is None or self._vector_store is None:
            return report
        embedding = self._vector_store.get_report_embedding(report.id)
        if embedding is None:
            return report
        return report.model_copy(update={"embedding": embedding})

    @staticmethod
    def _model_from_item(model: type[Any], item: dict[str, Any] | None) -> Any | None:
        if item is None:
            return None
        return model.model_validate(item["document"])

    @staticmethod
    def _key(entity_type: str, entity_id: str) -> dict[str, str]:
        return {
            "PK": f"{entity_type}#{entity_id}",
            "SK": f"{entity_type}#{entity_id}",
        }


def _to_dynamodb_value(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [_to_dynamodb_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_dynamodb_value(item) for key, item in value.items()}
    return value


def _from_dynamodb_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)
    if isinstance(value, list):
        return [_from_dynamodb_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _from_dynamodb_value(item) for key, item in value.items()}
    return value
