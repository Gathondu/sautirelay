from __future__ import annotations

import re
from dataclasses import asdict, dataclass


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}(?!\w)"
)
_COORDINATE_PAIR_RE = re.compile(r"(?<!\d)-?\d{1,2}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}(?!\d)")
_PRECISE_PLACE_RE = re.compile(
    r"\b(?:behind|inside|at|next to|opposite)\s+[^.?!,;]{1,80}?"
    r"\b(?:shelter|house|home|room|tent|compound|gate|door|block)\b",
    re.IGNORECASE,
)
_LANDMARK_RE = re.compile(
    r"\b(?:borehole|water point|well|clinic|market|bridge|school|camp block)\b",
    re.IGNORECASE,
)
_PERSON_WITH_TITLE_RE = re.compile(
    r"\b(?:Mr|Mrs|Ms|Dr|Chief|Pastor|Imam|Sheikh|Elder)\.?\s+[A-Z][a-zA-Z'-]{2,}\b"
)
_TWO_NAME_RE = re.compile(r"\b[A-Z][a-zA-Z'-]{2,}\s+[A-Z][a-zA-Z'-]{2,}\b")
_SINGLE_NAME_CONTEXT_RE = re.compile(
    r"\b(?:called|named|by|from)\s+([A-Z][a-zA-Z'-]{2,})\b"
)
_NAME_BEFORE_CONTEXT_RE = re.compile(
    r"\b([A-Z][a-zA-Z'-]{2,})\s+(?:from|called|emailed|reported|said)\b"
)
_POSSESSIVE_NAME_RE = re.compile(r"\b[A-Z][a-zA-Z'-]{2,}'s\b")


@dataclass(frozen=True)
class RedactionResult:
    redacted_text: str
    sensitive_types: list[str]
    changed: bool

    def __contains__(self, value: str) -> bool:
        return value in self.redacted_text

    def __str__(self) -> str:
        return self.redacted_text

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def redact_sensitive_info(text: str | None) -> RedactionResult:
    """Remove obvious PII and precise location clues from reporter text."""

    source = text or ""
    redacted = source
    sensitive_types: list[str] = []

    redacted, found = _replace(redacted, _EMAIL_RE, "[EMAIL]")
    if found:
        sensitive_types.append("email")

    redacted, found = _replace(redacted, _PHONE_RE, "[PHONE]")
    if found:
        sensitive_types.append("phone")

    redacted, found = _replace(redacted, _COORDINATE_PAIR_RE, "[APPROXIMATE_LOCATION]")
    if found:
        sensitive_types.append("coordinates")

    redacted, found = _replace(redacted, _PERSON_WITH_TITLE_RE, "[PERSON]")
    if found:
        sensitive_types.append("person_name")

    redacted, found = _replace(redacted, _TWO_NAME_RE, "[PERSON]")
    if found:
        sensitive_types.append("person_name")

    def replace_single_name(match: re.Match[str]) -> str:
        return match.group(0).replace(match.group(1), "[PERSON]")

    redacted, count = _SINGLE_NAME_CONTEXT_RE.subn(replace_single_name, redacted)
    if count:
        sensitive_types.append("person_name")

    def replace_name_before_context(match: re.Match[str]) -> str:
        return match.group(0).replace(match.group(1), "[PERSON]")

    redacted, count = _NAME_BEFORE_CONTEXT_RE.subn(replace_name_before_context, redacted)
    if count:
        sensitive_types.append("person_name")

    redacted, found = _replace(redacted, _POSSESSIVE_NAME_RE, "[PERSON]'s")
    if found:
        sensitive_types.append("person_name")

    redacted, found = _replace(redacted, _PRECISE_PLACE_RE, "[PRECISE_LOCATION]")
    if found:
        sensitive_types.append("precise_location")

    redacted, found = _replace(redacted, _LANDMARK_RE, "[RESOURCE_POINT]")
    if found:
        sensitive_types.append("landmark")

    unique_types = list(dict.fromkeys(sensitive_types))
    return RedactionResult(
        redacted_text=redacted.strip(),
        sensitive_types=unique_types,
        changed=redacted != source,
    )


def safe_location_view(location: object, visibility: str = "mediator") -> dict[str, object]:
    """Return the coarsest useful location shape for a viewer type."""

    data = _as_dict(location)
    if not data:
        return {"area": "Approximate area unavailable", "precision": "unknown"}

    visibility_key = f"{visibility}_area"
    area = (
        data.get(visibility_key)
        or data.get("analytics_area")
        or data.get("internal_area")
        or data.get("admin_level_2")
        or data.get("admin_level_1")
        or data.get("country")
        or data.get("manualDescription")
        or data.get("raw_location")
        or data.get("raw_location_text")
        or "Approximate area only"
    )
    precision = data.get("location_precision") or data.get("precision") or "coarse"
    return {"area": str(area), "precision": str(precision)}


def contains_sensitive_terms(text: str | None) -> bool:
    result = redact_sensitive_info(text)
    return result.changed


def _replace(text: str, pattern: re.Pattern[str], replacement: str) -> tuple[str, bool]:
    value, count = pattern.subn(replacement, text)
    return value, count > 0


def _as_dict(value: object) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if hasattr(value, "__dict__"):
        return vars(value)
    return {}
