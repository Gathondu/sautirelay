from __future__ import annotations

import importlib
from typing import Any

import pytest


def require_attr(module_name: str, attr_name: str) -> Any:
    module = importlib.import_module(module_name)
    attr = getattr(module, attr_name, None)
    assert attr is not None, f"{module_name}.{attr_name} must be implemented"
    return attr


def test_privacy_redaction_removes_direct_identifiers() -> None:
    redact_sensitive_info = require_attr("backend.app.services.privacy", "redact_sensitive_info")

    redacted = redact_sensitive_info(
        "John from Block C called +254712345678 and emailed john@example.com. "
        "The group is near Amina's shelter behind the exact borehole."
    )

    assert "John" not in redacted
    assert "Amina" not in redacted
    assert "+254712345678" not in redacted
    assert "john@example.com" not in redacted
    assert "[PERSON]" in redacted


@pytest.mark.parametrize(
    ("category", "urgency", "similar_count", "expected_minimum"),
    [
        ("COMMUNITY_RUMOR", "NOT_SURE", 0, "LOW"),
        ("WATER_OR_RESOURCE_CONFLICT", "WITHIN_24_HOURS", 0, "HIGH"),
        ("DISPLACEMENT_RISK", "WITHIN_24_HOURS", 2, "CRITICAL"),
    ],
)
def test_risk_scoring_is_explainable_and_human_reviewable(
    category: str,
    urgency: str,
    similar_count: int,
    expected_minimum: str,
) -> None:
    score_risk = require_attr("backend.app.services.risk", "score_risk")

    result = score_risk(
        category=category,
        urgency=urgency,
        similar_report_count=similar_count,
        text="There may be violence tomorrow near a water point.",
    )

    rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    assert rank[result.risk_level] >= rank[expected_minimum]
    assert result.reasons
    assert all(isinstance(reason, str) and reason for reason in result.reasons)


def test_ai_structured_output_fallback_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    intake_service_cls = require_attr("backend.app.services.ai_intake", "AIIntakeService")

    class FailingClient:
        class responses:
            @staticmethod
            def parse(*_: Any, **__: Any) -> None:
                raise RuntimeError("model unavailable")

    service = intake_service_cls(client=FailingClient())
    result = service.process_report(
        text="There are rumors of violence near the water point tomorrow.",
        language="en",
        location={"country": "Mali", "area": "Mopti"},
    )

    assert result.needs_human_review is True
    assert result.confidence <= 0.5
    assert result.summary
    assert result.category in {"NOT_SURE", "COMMUNITY_RUMOR", "OTHER"}


def test_embedding_similarity_clusters_related_reports() -> None:
    cluster_reports = require_attr("backend.app.services.clustering", "cluster_reports")

    reports = [
        {
            "id": "report-1",
            "text": "Herders may be blocked at the water point tomorrow.",
            "embedding": [0.99, 0.01, 0.0],
            "category": "WATER_OR_RESOURCE_CONFLICT",
            "area": "Mopti",
        },
        {
            "id": "report-2",
            "text": "Young men are gathering near the borehole after market day.",
            "embedding": [0.98, 0.02, 0.0],
            "category": "WATER_OR_RESOURCE_CONFLICT",
            "area": "Mopti",
        },
        {
            "id": "report-3",
            "text": "Families were asked to pay before receiving aid.",
            "embedding": [0.0, 0.0, 1.0],
            "category": "AID_DIVERSION",
            "area": "Goma",
        },
    ]

    clusters = cluster_reports(reports, similarity_threshold=0.9)
    related_cluster = next(
        cluster for cluster in clusters if {"report-1", "report-2"}.issubset(set(cluster.report_ids))
    )

    assert related_cluster.report_count == 2
    assert "report-3" not in related_cluster.report_ids


def test_workflow_transition_rules_prevent_unverified_escalation() -> None:
    workflow = require_attr("backend.app.services.workflow", "WorkflowRules")
    rules = workflow()

    assert rules.can_escalate_report("VERIFIED") is True
    assert rules.can_escalate_report("PENDING_REVIEW") is False
    assert rules.can_transition_report("PENDING_REVIEW", "VERIFIED") is True
    assert rules.can_transition_escalation("ESCALATED", "ACCEPTED") is True
    assert rules.can_transition_escalation("RESOLVED", "ACCEPTED") is False
