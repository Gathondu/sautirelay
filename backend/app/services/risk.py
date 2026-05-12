from __future__ import annotations

from dataclasses import asdict, dataclass


RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

HIGH_RISK_CATEGORIES = {
    "WATER_OR_RESOURCE_CONFLICT",
    "HATE_SPEECH_OR_INCITEMENT",
    "ARMED_GROUP_MOVEMENT",
    "ELECTION_INTIMIDATION",
    "DISPLACEMENT_RISK",
    "GBV_OR_PROTECTION_RISK",
    "POLICE_OR_SECURITY_ABUSE",
}

MEDIUM_RISK_CATEGORIES = {
    "LAND_CONFLICT",
    "AID_DIVERSION",
    "RESOURCE_EXPLOITATION",
    "PUBLIC_SERVICE_FAILURE",
    "COMMUNITY_RUMOR",
}

TIME_URGENCY = {
    "IMMEDIATE": 35,
    "NOW": 35,
    "WITHIN_24_HOURS": 28,
    "TODAY": 25,
    "THIS_WEEK": 15,
    "UNKNOWN": 5,
    "NOT_SURE": 5,
}


@dataclass(frozen=True)
class RiskAssessment:
    score: int
    risk_level: str
    urgency: str
    reasons: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def score_risk(
    *,
    category: str | None = None,
    urgency: str | None = None,
    text: str | None = None,
    similar_report_count: int = 0,
    immediate_danger: bool | None = None,
    sensitive_group: bool = False,
    confidence: float | None = None,
) -> RiskAssessment:
    """Explainable, deterministic risk score for human review queues."""

    normalized_category = _normalize(category, default="NOT_SURE")
    normalized_urgency = infer_urgency(text=text, explicit_urgency=urgency)
    score = 0
    reasons: list[str] = []

    if normalized_category in HIGH_RISK_CATEGORIES:
        score += 30
        reasons.append("Category is associated with direct safety or protection risk.")
    elif normalized_category in MEDIUM_RISK_CATEGORIES:
        score += 14
        reasons.append("Category can escalate without local intervention.")
    else:
        score += 6
        reasons.append("Category is unclear and needs human review.")

    urgency_score = TIME_URGENCY.get(normalized_urgency, 5)
    score += urgency_score
    if urgency_score >= 25:
        reasons.append("Timeframe suggests action may be needed within 24 hours.")
    elif urgency_score >= 15:
        reasons.append("Timeframe suggests the signal may develop this week.")

    if immediate_danger:
        score += 30
        reasons.append("Reporter indicated immediate danger.")

    if similar_report_count >= 2:
        score += 25
        reasons.append("Multiple related reports were found nearby or in the same theme.")
    elif similar_report_count >= 1:
        score += 12
        reasons.append("At least one related report was found.")

    if sensitive_group:
        score += 10
        reasons.append("The report may involve a vulnerable or protected group.")

    if confidence is not None and confidence < 0.45:
        score -= 5
        reasons.append("AI confidence is low, so human verification is especially important.")

    score = max(0, min(100, score))
    return RiskAssessment(
        score=score,
        risk_level=risk_label(score),
        urgency=normalized_urgency,
        reasons=reasons,
    )


def risk_label(score: int | float) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 55:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def infer_urgency(text: str | None = None, explicit_urgency: str | None = None) -> str:
    if explicit_urgency:
        return _normalize_urgency(explicit_urgency)

    body = (text or "").lower()
    if any(term in body for term in ("now", "right now", "immediate", "currently", "ongoing")):
        return "IMMEDIATE"
    if any(term in body for term in ("tomorrow", "tonight", "today", "24 hours", "within 24")):
        return "WITHIN_24_HOURS"
    if any(term in body for term in ("this week", "market day", "next few days")):
        return "THIS_WEEK"
    return "UNKNOWN"


def _normalize(value: str | None, *, default: str) -> str:
    if not value:
        return default
    return value.strip().upper().replace(" ", "_").replace("-", "_")


def _normalize_urgency(value: str) -> str:
    normalized = _normalize(value, default="UNKNOWN")
    aliases = {
        "HIGH": "WITHIN_24_HOURS",
        "IMMEDIATE_DANGER": "IMMEDIATE",
        "LOW": "UNKNOWN",
        "MEDIUM": "THIS_WEEK",
        "NOT_SURE": "UNKNOWN",
    }
    return aliases.get(normalized, normalized)
