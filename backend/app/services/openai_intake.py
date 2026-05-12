from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field

from .clustering import EmbeddingService
from .privacy import redact_sensitive_info, safe_location_view
from .risk import score_risk

DEFAULT_INTAKE_MODEL = "gpt-5.5"

REPORT_CATEGORIES = (
    "LAND_CONFLICT",
    "WATER_OR_RESOURCE_CONFLICT",
    "HATE_SPEECH_OR_INCITEMENT",
    "ARMED_GROUP_MOVEMENT",
    "ELECTION_INTIMIDATION",
    "DISPLACEMENT_RISK",
    "GBV_OR_PROTECTION_RISK",
    "POLICE_OR_SECURITY_ABUSE",
    "AID_DIVERSION",
    "PUBLIC_SERVICE_FAILURE",
    "RESOURCE_EXPLOITATION",
    "COMMUNITY_RUMOR",
    "OTHER",
    "NOT_SURE",
)


class IntakeStructuredOutput(BaseModel):
    language: str = Field(default="unknown")
    translated_text: str = Field(default="")
    category: str = Field(default="NOT_SURE")
    urgency: str = Field(default="UNKNOWN")
    risk_level: str = Field(default="LOW")
    confidence_score: float = Field(default=0.35, ge=0.0, le=1.0)
    summary: str = Field(default="")
    redacted_text: str = Field(default="")
    recommended_verifier_action: str = Field(default="Human review recommended.")
    recommended_mediator_action: str = Field(default="Wait for verifier decision before action.")
    safety_warnings: list[str] = Field(default_factory=list)
    needs_human_review: bool = Field(default=True)
    reasoning_summary: str = Field(default="Deterministic local fallback.")


class MediatorBriefStructuredOutput(BaseModel):
    title: str = Field(default="SautiRelay Alert")
    risk_type: str = Field(default="NOT_SURE")
    risk_level: str = Field(default="LOW")
    time_sensitivity: str = Field(default="Unknown")
    area: str = Field(default="Approximate area only")
    summary: str = Field(default="")
    recommended_response: list[str] = Field(default_factory=list)
    safety_note: str = Field(default="Do not disclose reporter details.")
    follow_up_prompt: str = Field(default="Record field notes and outcome after action.")


@dataclass(frozen=True)
class IntakeResult:
    language: str
    translated_text: str
    category: str
    urgency: str
    risk_level: str
    confidence_score: float
    summary: str
    redacted_text: str
    recommended_verifier_action: str
    recommended_mediator_action: str
    safety_warnings: list[str]
    needs_human_review: bool
    reasoning_summary: str
    embedding: list[float]
    provider: str

    @property
    def confidence(self) -> float:
        return self.confidence_score

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MediatorBrief:
    title: str
    risk_type: str
    risk_level: str
    time_sensitivity: str
    area: str
    summary: str
    recommended_response: list[str]
    safety_note: str
    follow_up_prompt: str
    provider: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OpenAIIntakeService:
    """AI intake facade with OpenAI Responses API and safe local fallbacks."""

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        client: OpenAI | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.model = model or os.getenv("SAUTIRELAY_OPENAI_MODEL", DEFAULT_INTAKE_MODEL)
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.client = client
        self.embedding_service = embedding_service or EmbeddingService(api_key=self.api_key)

    def process_report(
        self,
        *,
        text: str,
        language: str | None = None,
        location: object | None = None,
        category_hint: str | None = None,
        urgency_hint: str | None = None,
    ) -> IntakeResult:
        if self.api_key or self.client is not None:
            try:
                parsed = self._process_with_openai(
                    text=text,
                    language=language,
                    location=location,
                    category_hint=category_hint,
                    urgency_hint=urgency_hint,
                )
                return self._result_from_structured(parsed, text=text, provider="openai")
            except Exception:
                pass
        return self._fallback_process_report(
            text=text,
            language=language,
            location=location,
            category_hint=category_hint,
            urgency_hint=urgency_hint,
        )

    def generate_mediator_brief(
        self,
        *,
        signal: object,
        reports: list[object] | None = None,
        safety_note: str | None = None,
    ) -> MediatorBrief:
        if self.api_key or self.client is not None:
            try:
                parsed = self._brief_with_openai(signal=signal, reports=reports or [], safety_note=safety_note)
                return self._brief_from_structured(parsed, provider="openai")
            except Exception:
                pass
        return self._fallback_mediator_brief(signal=signal, reports=reports or [], safety_note=safety_note)

    def _process_with_openai(
        self,
        *,
        text: str,
        language: str | None,
        location: object | None,
        category_hint: str | None,
        urgency_hint: str | None,
    ) -> IntakeStructuredOutput:
        client = self.client or OpenAI(api_key=self.api_key)
        location_view = safe_location_view(location, visibility="mediator")
        response = client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": _INTAKE_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "report_text": text,
                            "language_hint": language,
                            "category_hint": category_hint,
                            "urgency_hint": urgency_hint,
                            "safe_location": location_view,
                        },
                        ensure_ascii=True,
                    ),
                },
            ],
            text_format=IntakeStructuredOutput,
        )
        parsed = _extract_parsed_response(response)
        if not isinstance(parsed, IntakeStructuredOutput):
            raise ValueError("OpenAI intake response did not match IntakeStructuredOutput.")
        return parsed

    def _brief_with_openai(
        self,
        *,
        signal: object,
        reports: list[object],
        safety_note: str | None,
    ) -> MediatorBriefStructuredOutput:
        client = self.client
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
        response = client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": _MEDIATOR_BRIEF_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "signal": _public_dict(signal),
                            "reports": [_public_dict(report) for report in reports],
                            "safety_note": safety_note,
                        },
                        ensure_ascii=True,
                    ),
                },
            ],
            text_format=MediatorBriefStructuredOutput,
        )
        parsed = _extract_parsed_response(response)
        if not isinstance(parsed, MediatorBriefStructuredOutput):
            raise ValueError("OpenAI brief response did not match MediatorBriefStructuredOutput.")
        return parsed

    def _fallback_process_report(
        self,
        *,
        text: str,
        language: str | None,
        location: object | None,
        category_hint: str | None,
        urgency_hint: str | None,
    ) -> IntakeResult:
        redaction = redact_sensitive_info(text)
        category = _normalize_category(category_hint) or _infer_category(text)
        risk = score_risk(
            category=category,
            urgency=urgency_hint,
            text=text,
            immediate_danger=_mentions_immediate_danger(text),
            sensitive_group=_mentions_sensitive_group(text),
        )
        summary = _summarize(redaction.redacted_text)
        translated_text = text.strip()
        embedding = self.embedding_service.embed_text(f"{category} {summary} {redaction.redacted_text}")
        warnings = ["Do not disclose reporter details."]
        if redaction.changed:
            warnings.append("Sensitive details were redacted before review.")
        if location:
            warnings.append("Use approximate location only for mediator action.")

        return IntakeResult(
            language=language or _detect_language(text),
            translated_text=translated_text,
            category=category,
            urgency=risk.urgency,
            risk_level=risk.risk_level,
            confidence_score=0.45,
            summary=summary,
            redacted_text=redaction.redacted_text,
            recommended_verifier_action=_recommended_verifier_action(risk.risk_level),
            recommended_mediator_action=_recommended_mediator_action(category, risk.risk_level),
            safety_warnings=warnings,
            needs_human_review=True,
            reasoning_summary="; ".join(risk.reasons),
            embedding=embedding,
            provider="deterministic",
        )

    def _result_from_structured(self, parsed: IntakeStructuredOutput, *, text: str, provider: str) -> IntakeResult:
        local_redaction = redact_sensitive_info(parsed.redacted_text or text)
        category = _normalize_category(parsed.category) or "NOT_SURE"
        risk = score_risk(
            category=category,
            urgency=parsed.urgency,
            text=text,
            confidence=parsed.confidence_score,
        )
        embedding = self.embedding_service.embed_text(
            f"{category} {parsed.summary} {local_redaction.redacted_text or parsed.translated_text}"
        )
        warnings = list(parsed.safety_warnings)
        if local_redaction.changed and "Sensitive details were redacted before review." not in warnings:
            warnings.append("Sensitive details were redacted before review.")

        return IntakeResult(
            language=parsed.language,
            translated_text=parsed.translated_text or text,
            category=category,
            urgency=risk.urgency,
            risk_level=risk.risk_level,
            confidence_score=float(parsed.confidence_score),
            summary=parsed.summary or _summarize(local_redaction.redacted_text),
            redacted_text=local_redaction.redacted_text,
            recommended_verifier_action=parsed.recommended_verifier_action,
            recommended_mediator_action=parsed.recommended_mediator_action,
            safety_warnings=warnings,
            needs_human_review=True,
            reasoning_summary=parsed.reasoning_summary,
            embedding=embedding,
            provider=provider,
        )

    def _brief_from_structured(self, parsed: MediatorBriefStructuredOutput, *, provider: str) -> MediatorBrief:
        return MediatorBrief(
            title=parsed.title,
            risk_type=_normalize_category(parsed.risk_type) or "NOT_SURE",
            risk_level=parsed.risk_level.upper(),
            time_sensitivity=parsed.time_sensitivity,
            area=parsed.area,
            summary=redact_sensitive_info(parsed.summary).redacted_text,
            recommended_response=parsed.recommended_response,
            safety_note=parsed.safety_note or "Do not disclose reporter details.",
            follow_up_prompt=parsed.follow_up_prompt,
            provider=provider,
        )

    def _fallback_mediator_brief(
        self,
        *,
        signal: object,
        reports: list[object],
        safety_note: str | None,
    ) -> MediatorBrief:
        category = _normalize_category(_get(signal, "category")) or "NOT_SURE"
        risk_level = str(_get(signal, "risk_level", "LOW")).upper()
        summary = _get(signal, "summary") or _fallback_signal_summary(signal, reports)
        redacted_summary = redact_sensitive_info(str(summary)).redacted_text
        area = _get(signal, "area") or safe_location_view(_get(signal, "location"), visibility="mediator")["area"]

        return MediatorBrief(
            title="SautiRelay Alert",
            risk_type=category,
            risk_level=risk_level,
            time_sensitivity=_time_sensitivity_for(signal),
            area=str(area or "Approximate area only"),
            summary=redacted_summary,
            recommended_response=_mediator_steps(category),
            safety_note=safety_note or "Do not disclose reporter details or accuse any group publicly before verification.",
            follow_up_prompt="Record field notes, action taken, outcome, and whether follow-up is required.",
            provider="deterministic",
        )


def process_report_intake(**kwargs: Any) -> IntakeResult:
    return OpenAIIntakeService().process_report(**kwargs)


def generate_mediator_brief(**kwargs: Any) -> MediatorBrief:
    return OpenAIIntakeService().generate_mediator_brief(**kwargs)


def _extract_parsed_response(response: object) -> object:
    parsed = getattr(response, "output_parsed", None)
    if parsed is not None:
        return parsed

    for output in getattr(response, "output", []) or []:
        if getattr(output, "type", None) != "message":
            continue
        for item in getattr(output, "content", []) or []:
            if getattr(item, "type", None) == "refusal":
                raise ValueError(getattr(item, "refusal", "OpenAI refused the structured output request."))
            parsed = getattr(item, "parsed", None)
            if parsed is not None:
                return parsed
    raise ValueError("OpenAI response did not include parsed structured output.")


def _normalize_category(value: object) -> str | None:
    if not value:
        return None
    normalized = str(value).strip().upper().replace(" ", "_").replace("-", "_")
    aliases = {
        "CONFLICT_RISK": "COMMUNITY_RUMOR",
        "PUBLIC_SERVICE": "PUBLIC_SERVICE_FAILURE",
        "DISPLACEMENT": "DISPLACEMENT_RISK",
        "GBV_REFERRAL": "GBV_OR_PROTECTION_RISK",
        "RESOURCE_PROTECTION": "RESOURCE_EXPLOITATION",
        "UNSURE": "NOT_SURE",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in REPORT_CATEGORIES else "NOT_SURE"


def _infer_category(text: str) -> str:
    body = text.lower()
    if any(keyword in body for keyword in ("rumor", "rumors", "heard", "people say")):
        return "COMMUNITY_RUMOR"
    category_keywords = [
        ("WATER_OR_RESOURCE_CONFLICT", ("water", "well", "borehole", "herder", "pastoral", "resource")),
        ("LAND_CONFLICT", ("land", "farm", "boundary", "eviction")),
        ("HATE_SPEECH_OR_INCITEMENT", ("hate", "chased away", "incite", "speech", "voice note")),
        ("ARMED_GROUP_MOVEMENT", ("armed", "militia", "weapon", "fighters")),
        ("ELECTION_INTIMIDATION", ("election", "polling", "opposition", "vote")),
        ("DISPLACEMENT_RISK", ("leaving", "displaced", "camp", "families are leaving", "refugee")),
        ("GBV_OR_PROTECTION_RISK", ("gbv", "assault", "protection", "women", "girls")),
        ("POLICE_OR_SECURITY_ABUSE", ("police", "security abuse", "beaten", "arrest")),
        ("AID_DIVERSION", ("aid", "distribution", "supplies", "pay before receiving")),
        ("PUBLIC_SERVICE_FAILURE", ("clinic", "school", "service", "water service")),
        ("RESOURCE_EXPLOITATION", ("mining", "logging", "exploitation", "oil")),
        ("COMMUNITY_RUMOR", ("rumor", "heard", "people say")),
    ]
    for category, keywords in category_keywords:
        if any(keyword in body for keyword in keywords):
            return category
    return "NOT_SURE"


def _detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06ff]", text):
        return "Arabic"
    if any(word in text.lower() for word in ("bonjour", "merci", "avec", "dans")):
        return "French"
    if any(word in text.lower() for word in ("habari", "maji", "watu", "kesho")):
        return "Kiswahili"
    if any(word in text.lower() for word in ("obrigado", "amanha", "comunidade")):
        return "Portuguese"
    return "English"


def _summarize(text: str, *, max_words: int = 28) -> str:
    words = text.strip().split()
    if not words:
        return "Anonymous report requires human review."
    summary = " ".join(words[:max_words])
    if len(words) > max_words:
        summary += "..."
    return summary


def _mentions_immediate_danger(text: str) -> bool:
    return any(term in text.lower() for term in ("attack", "violence", "danger", "armed", "tonight", "tomorrow"))


def _mentions_sensitive_group(text: str) -> bool:
    return any(term in text.lower() for term in ("women", "children", "girls", "refugee", "idp", "displaced"))


def _recommended_verifier_action(risk_level: str) -> str:
    if risk_level in {"HIGH", "CRITICAL"}:
        return "Prioritize human verification and check for related reports before mediator escalation."
    return "Review redacted report, confirm category and location precision, then decide next status."


def _recommended_mediator_action(category: str, risk_level: str) -> str:
    if risk_level in {"HIGH", "CRITICAL"}:
        return "Prepare a concise mediator brief after verifier approval."
    if category == "AID_DIVERSION":
        return "If verified, route to a trusted humanitarian accountability mediator."
    return "No mediator action until a verifier marks the signal as verified."


def _mediator_steps(category: str) -> list[str]:
    defaults = [
        "Review the anonymized action brief.",
        "Coordinate with trusted local peace actors.",
        "Record outcome and follow-up needs.",
    ]
    by_category = {
        "WATER_OR_RESOURCE_CONFLICT": [
            "Contact the local water committee.",
            "Engage youth and women peacebuilders.",
            "Convene preventive dialogue before the reported timeframe.",
        ],
        "HATE_SPEECH_OR_INCITEMENT": [
            "Verify the message with trusted community media partners.",
            "Support calm public messaging without naming alleged perpetrators.",
            "Track whether inflammatory language continues.",
        ],
        "AID_DIVERSION": [
            "Contact a trusted humanitarian accountability partner.",
            "Check distribution concerns without exposing reporters.",
            "Record whether access was restored or follow-up is needed.",
        ],
        "DISPLACEMENT_RISK": [
            "Coordinate with a protection partner.",
            "Verify movement constraints and immediate needs.",
            "Record follow-up requirements within the next review window.",
        ],
    }
    return by_category.get(category, defaults)


def _time_sensitivity_for(signal: object) -> str:
    urgency = str(_get(signal, "urgency", "")).upper()
    if urgency in {"IMMEDIATE", "NOW"}:
        return "Immediate"
    if urgency in {"WITHIN_24_HOURS", "TODAY"}:
        return "24 hours"
    if urgency == "THIS_WEEK":
        return "This week"
    return "Unknown"


def _fallback_signal_summary(signal: object, reports: list[object]) -> str:
    def safe_int(val, default=1) -> int:
        try:
            return int(val)
        except (TypeError, ValueError):
            return default
    report_count = len(reports) if reports else safe_int(_get(signal, "report_count", 1))
    category = _normalize_category(_get(signal, "category")) or "NOT_SURE"
    return (
        f"{report_count} anonymous signal(s) indicate a possible "
        f"{category.lower().replace('_', ' ')} concern. Human verification has approved mediator follow-up."
    )


def _public_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        data = dict(value)
    elif hasattr(value, "to_dict"):
        data = getattr(value, 'to_dict')()
    elif hasattr(value, "model_dump"):
        data = getattr(value, 'model_dump')()
    elif hasattr(value, "dict"):
        data = getattr(value, 'dict')()
    elif hasattr(value, "__dict__"):
        data = vars(value)
    else:
        data = {"value": str(value)}

    for key in ("raw_text", "raw_text_encrypted", "raw_location", "raw_location_encrypted", "reporter_identity"):
        data.pop(key, None)
    if "summary" in data:
        data["summary"] = redact_sensitive_info(str(data["summary"])).redacted_text
    if "text" in data:
        data["text"] = redact_sensitive_info(str(data["text"])).redacted_text
    return data


def _get(value: object, key: str, default: object = None) -> object:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


_INTAKE_SYSTEM_PROMPT = """You support SautiRelay, a privacy-first early-warning platform.
Return only the requested structured output. Classify, translate to English when useful,
redact personal and precise location details, summarize, estimate risk and urgency, and
suggest verifier and mediator actions. AI is advisory only: always set needs_human_review
to true and never make final truth, guilt, or escalation decisions."""

_MEDIATOR_BRIEF_SYSTEM_PROMPT = """Create a concise, anonymized SautiRelay mediator action brief.
Do not include reporter identity, phone numbers, exact GPS, unredacted names, or public accusations.
Use mediator naming. Recommend peaceful, preventive, community-based action only."""
