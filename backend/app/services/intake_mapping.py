"""Map OpenAI intake dataclass output onto persisted report fields."""

from __future__ import annotations

from backend.app.core.models import ReportCategory, RiskLevel, Urgency
from backend.app.services.openai_intake import IntakeResult as OpenAIIntakeResult


def coerce_report_category(label: str) -> ReportCategory:
    normalized = label.strip().upper().replace("-", "_")
    for member in ReportCategory:
        if member.value == normalized:
            return member
    return ReportCategory.not_sure


def coerce_urgency(label: str) -> Urgency:
    normalized = label.strip().upper().replace("-", "_")
    if normalized == "IMMEDIATE":
        return Urgency.within_24_hours
    for member in Urgency:
        if member.value == normalized:
            return member
    return Urgency.unknown


def coerce_risk_level(label: str) -> RiskLevel:
    normalized = label.strip().upper().replace("-", "_")
    for member in RiskLevel:
        if member.value == normalized:
            return member
    return RiskLevel.medium


def openai_intake_to_report_updates(result: OpenAIIntakeResult) -> dict[str, object]:
    embedding: list[float] | None = None
    if result.embedding:
        embedding = [float(value) for value in result.embedding]

    return {
        "redacted_text": result.redacted_text,
        "translated_text": result.translated_text,
        "summary": result.summary,
        "category": coerce_report_category(result.category),
        "urgency": coerce_urgency(result.urgency),
        "risk_level": coerce_risk_level(result.risk_level),
        "confidence_score": float(result.confidence_score),
        "ai_recommended_mediator_action": result.recommended_mediator_action,
        "ai_safety_warnings": list(result.safety_warnings),
        "needs_human_review": result.needs_human_review,
        "embedding": embedding,
    }
