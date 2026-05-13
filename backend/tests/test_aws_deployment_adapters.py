from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from backend.app.core.models import (
    ApproximateLocation,
    ReportCategory,
    ReportDocument,
    ReportStatus,
    RiskLevel,
    Urgency,
)
from backend.app.repositories.dynamodb import DynamoDbSautiRelayRepository
from backend.app.services.s3_vectors import S3VectorStore, validate_s3_vectors_region


class FakeDynamoTable:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict[str, Any]] = {}

    def put_item(self, *, Item: dict[str, Any]) -> None:
        self.items[(Item["PK"], Item["SK"])] = Item

    def get_item(self, *, Key: dict[str, str]) -> dict[str, Any]:
        item = self.items.get((Key["PK"], Key["SK"]))
        return {"Item": item} if item is not None else {}

    def delete_item(self, *, Key: dict[str, str]) -> None:
        self.items.pop((Key["PK"], Key["SK"]), None)

    def scan(self, **kwargs: Any) -> dict[str, Any]:
        values = kwargs.get("ExpressionAttributeValues") or {}
        entity_type = values.get(":entity_type")
        items = list(self.items.values())
        if entity_type is not None:
            items = [item for item in items if item.get("entityType") == entity_type]
        return {"Items": items}

    def query(self, **kwargs: Any) -> dict[str, Any]:
        values = kwargs.get("ExpressionAttributeValues") or {}
        gsi1_pk = values.get(":tracking_pk")
        items = [item for item in self.items.values() if item.get("GSI1PK") == gsi1_pk]
        return {"Items": items[: kwargs.get("Limit", len(items))]}


class FakeVectorStore:
    def __init__(self) -> None:
        self.embeddings: dict[str, list[float]] = {}

    def put_report_embedding(self, *, report_id: str, embedding: list[float], metadata: dict[str, object]) -> None:
        self.embeddings[report_id] = embedding

    def get_report_embedding(self, report_id: str) -> list[float] | None:
        return self.embeddings.get(report_id)


class FakeS3VectorsClient:
    def __init__(self) -> None:
        self.put_payload: dict[str, Any] | None = None

    def put_vectors(self, **kwargs: Any) -> dict[str, Any]:
        self.put_payload = kwargs
        return {}

    def get_vectors(self, **kwargs: Any) -> dict[str, Any]:
        return {"vectors": [{"key": kwargs["keys"][0], "data": {"float32": [0.1, 0.2, 0.3]}}]}

    def query_vectors(self, **kwargs: Any) -> dict[str, Any]:
        return {"vectors": [{"key": "report_1", "distance": 0.01, "metadata": {"category": "OTHER"}}]}


def test_dynamodb_repository_stores_metadata_and_vectors_separately() -> None:
    table = FakeDynamoTable()
    vector_store = FakeVectorStore()
    repository = DynamoDbSautiRelayRepository(table=table, vector_store=vector_store)  # type: ignore[arg-type]
    report = _report()

    stored = _run(repository.put_report(report))
    by_id = _run(repository.get_report(report.id))
    by_tracking = _run(repository.get_report_by_tracking_code(report.public_tracking_code))
    reports = _run(repository.list_reports())

    assert stored.id == report.id
    assert by_id is not None
    assert by_id.embedding == [0.1, 0.2, 0.3]
    assert by_tracking is not None
    assert by_tracking.id == report.id
    assert reports[0].id == report.id
    dynamodb_item = next(iter(table.items.values()))
    assert "embedding" not in dynamodb_item["document"]
    assert vector_store.embeddings[report.id] == [0.1, 0.2, 0.3]


def test_s3_vector_store_validates_region_and_calls_client() -> None:
    client = FakeS3VectorsClient()
    store = S3VectorStore(
        vector_bucket_name="sautirelay-vectors",
        index_name="report-embeddings",
        region_name="af-south-1",
        client=client,
    )

    store.put_report_embedding(report_id="report_1", embedding=[0.1, 0.2, 0.3], metadata={"category": "OTHER"})

    assert client.put_payload == {
        "vectorBucketName": "sautirelay-vectors",
        "indexName": "report-embeddings",
        "vectors": [
            {
                "key": "report_1",
                "data": {"float32": [0.1, 0.2, 0.3]},
                "metadata": {"category": "OTHER"},
            }
        ],
    }
    assert store.get_report_embedding("report_1") == [0.1, 0.2, 0.3]
    assert store.query_similar_reports([0.1, 0.2, 0.3])[0]["key"] == "report_1"


def test_s3_vector_region_validation_rejects_unsupported_region() -> None:
    with pytest.raises(RuntimeError, match="S3 Vectors is not available"):
        validate_s3_vectors_region("antarctica-1")


def test_runtime_region_uses_non_reserved_lambda_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.app.core.config import get_settings

    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SAUTIRELAY_AWS_REGION", "af-south-1")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.aws_region == "af-south-1"


def test_lambda_handler_is_callable() -> None:
    from backend.app.lambda_handler import handler

    assert callable(handler)


def _report() -> ReportDocument:
    now = datetime(2026, 5, 13, tzinfo=UTC)
    return ReportDocument.model_validate(
        {
            "report_id": "report_1",
            "tracking_code": "SR-123456",
            "submitted_at": now,
            "channel": "pwa",
            "language": "en",
            "raw_text_encrypted": "local-encrypted::raw",
            "redacted_text": "redacted",
            "translated_text": "translated",
            "summary": "summary",
            "approximate_location": ApproximateLocation(country="Kenya", adminLevel1="Nairobi"),
            "category": ReportCategory.other,
            "urgency": Urgency.today,
            "risk_level": RiskLevel.medium,
            "confidence_score": 0.8,
            "reporter_anonymous": True,
            "status": ReportStatus.new,
            "embedding": [0.1, 0.2, 0.3],
            "created_at": now,
            "updated_at": now,
        }
    )


def _run(awaitable: Any) -> Any:
    import asyncio

    return asyncio.run(awaitable)
