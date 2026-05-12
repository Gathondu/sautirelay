"""Report intake, verification, and AI processing schemas."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from .common import (
    ApiModel,
    AuditEvent,
    Channel,
    LocationPrecision,
    LocationVisibility,
    ReportCategory,
    RiskLevel,
    Urgency,
)


class ReportStatus(str, Enum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    PENDING_REVIEW = "PENDING_REVIEW"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    VERIFIED = "VERIFIED"
    ESCALATED = "ESCALATED"
    DUPLICATE = "DUPLICATE"
    DISMISSED = "DISMISSED"
    ARCHIVED = "ARCHIVED"
    RESOLVED = "RESOLVED"


class ReporterSafeStatus(str, Enum):
    RECEIVED = "Received"
    UNDER_REVIEW = "Under review"
    VERIFIED = "Verified"
    ESCALATED_TO_TRUSTED_MEDIATOR = "Escalated to trusted mediator"
    CLOSED = "Closed"
    UNABLE_TO_VERIFY = "Unable to verify"


class VerificationDecision(str, Enum):
    VERIFIED = "VERIFIED"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    DUPLICATE = "DUPLICATE"
    UNVERIFIED_RUMOR = "UNVERIFIED_RUMOR"
    DISMISSED = "DISMISSED"
    ESCALATE_IMMEDIATELY = "ESCALATE_IMMEDIATELY"
    ARCHIVED = "ARCHIVED"


class VerificationEntityType(str, Enum):
    REPORT = "REPORT"
    CLUSTER = "CLUSTER"


class SafeLocationInput(ApiModel):
    area_description: str = Field(alias="areaDescription", min_length=2, max_length=500)
    precision: LocationPrecision
    country: str | None = Field(default=None, max_length=120)
    admin_level1: str | None = Field(default=None, alias="adminLevel1", max_length=160)
    admin_level2: str | None = Field(default=None, alias="adminLevel2", max_length=160)
    landmark: str | None = Field(default=None, max_length=240)


class ConsentInput(ApiModel):
    safety_notice_accepted: bool = Field(alias="safetyNoticeAccepted")
    data_use_accepted: bool = Field(alias="dataUseAccepted")
    share_with_mediator: bool = Field(alias="shareWithMediator")
    consent_version: str = Field(default="2026-05-12", alias="consentVersion")


class ReportCreateRequest(ApiModel):
    description: str = Field(min_length=10, max_length=5000)
    location: SafeLocationInput
    consent: ConsentInput
    channel: Channel = Channel.PWA
    language: str = Field(default="en", min_length=2, max_length=16)
    category_hint: ReportCategory | None = Field(default=None, alias="categoryHint")
    timeframe: Urgency = Urgency.UNKNOWN
    immediate_danger: bool = Field(default=False, alias="immediateDanger")


class ReportCreateResponse(ApiModel):
    report_id: str = Field(alias="reportId")
    tracking_code: str = Field(alias="trackingCode")
    status: ReportStatus
    safe_status: ReporterSafeStatus = Field(alias="safeStatus")
    message: str


class AiIntakeResult(ApiModel):
    category: ReportCategory
    risk_level: RiskLevel = Field(alias="riskLevel")
    urgency: Urgency
    summary: str
    redacted_text: str = Field(alias="redactedText")
    translated_text: str = Field(alias="translatedText")
    recommended_mediator_action: str = Field(alias="recommendedMediatorAction")
    confidence: float = Field(ge=0, le=1)
    needs_human_review: bool = Field(alias="needsHumanReview")
    safety_warnings: list[str] = Field(default_factory=list, alias="safetyWarnings")
    reasoning_summary: str = Field(alias="reasoningSummary")
    detected_language: str | None = Field(default=None, alias="detectedLanguage")


class ReportSummary(ApiModel):
    report_id: str = Field(alias="reportId")
    tracking_code: str = Field(alias="trackingCode")
    submitted_at: datetime = Field(alias="submittedAt")
    status: ReportStatus
    category: ReportCategory
    risk_level: RiskLevel = Field(alias="riskLevel")
    urgency: Urgency
    location: LocationVisibility
    ai_confidence: float = Field(alias="aiConfidence", ge=0, le=1)
    similar_report_count: int = Field(alias="similarReportCount", ge=0)


class ReportDetail(ReportSummary):
    channel: Channel
    language: str
    redacted_text: str = Field(alias="redactedText")
    translated_text: str = Field(alias="translatedText")
    ai_summary: str = Field(alias="aiSummary")
    safety_warnings: list[str] = Field(default_factory=list, alias="safetyWarnings")
    audit_events: list[AuditEvent] = Field(default_factory=list, alias="auditEvents")
    related_report_ids: list[str] = Field(default_factory=list, alias="relatedReportIds")


class ReportListResponse(ApiModel):
    items: list[ReportSummary]
    total: int = Field(ge=0)


class ReportStatusResponse(ApiModel):
    tracking_code: str = Field(alias="trackingCode")
    safe_status: ReporterSafeStatus = Field(alias="safeStatus")
    message: str


class ReportProcessResponse(ApiModel):
    report_id: str = Field(alias="reportId")
    status: ReportStatus
    intake: AiIntakeResult
    cluster_ids: list[str] = Field(default_factory=list, alias="clusterIds")


class VerificationRequest(ApiModel):
    decision: VerificationDecision
    notes: str = Field(min_length=1, max_length=3000)
    confidence: float = Field(ge=0, le=1)
    adjusted_category: ReportCategory | None = Field(default=None, alias="adjustedCategory")
    adjusted_risk_level: RiskLevel | None = Field(default=None, alias="adjustedRiskLevel")
    adjusted_location: LocationVisibility | None = Field(default=None, alias="adjustedLocation")
    recommended_mediator_id: str | None = Field(default=None, alias="recommendedMediatorId")
    safety_concerns: list[str] = Field(default_factory=list, alias="safetyConcerns")


class VerificationResponse(ApiModel):
    verification_id: str = Field(alias="verificationId")
    entity_type: VerificationEntityType = Field(alias="entityType")
    entity_id: str = Field(alias="entityId")
    decision: VerificationDecision
    status: str
    created_at: datetime = Field(alias="createdAt")
