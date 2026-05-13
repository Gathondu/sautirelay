from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, use_enum_values=True)


class UserRole(StrEnum):
    verifier = "verifier"
    mediator = "mediator"


class ReportStatus(StrEnum):
    new = "NEW"
    processing = "PROCESSING"
    pending_review = "PENDING_REVIEW"
    needs_more_info = "NEEDS_MORE_INFO"
    verified = "VERIFIED"
    escalated = "ESCALATED"
    duplicate = "DUPLICATE"
    unverified_rumor = "UNVERIFIED_RUMOR"
    dismissed = "DISMISSED"
    archived = "ARCHIVED"
    resolved = "RESOLVED"


class VerificationDecision(StrEnum):
    verified = "VERIFIED"
    needs_more_info = "NEEDS_MORE_INFO"
    duplicate = "DUPLICATE"
    unverified_rumor = "UNVERIFIED_RUMOR"
    dismissed = "DISMISSED"
    archive = "ARCHIVE"
    archived = "ARCHIVED"
    escalate_immediately = "ESCALATE_IMMEDIATELY"


class ClusterStatus(StrEnum):
    new = "NEW"
    pending_review = "PENDING_REVIEW"
    verified = "VERIFIED"
    escalated = "ESCALATED"
    dismissed = "DISMISSED"
    archived = "ARCHIVED"
    resolved = "RESOLVED"


class EscalationStatus(StrEnum):
    pending_acceptance = "PENDING_ACCEPTANCE"
    accepted = "ACCEPTED"
    action_recorded = "ACTION_RECORDED"
    resolved = "RESOLVED"
    follow_up_requested = "FOLLOW_UP_REQUESTED"


class OutcomeType(StrEnum):
    dialogue_held = "DIALOGUE_HELD"
    referred_to_partner = "REFERRED_TO_PARTNER"
    false_alarm = "FALSE_ALARM"
    risk_reduced = "RISK_REDUCED"
    violence_occurred = "VIOLENCE_OCCURRED"
    needs_follow_up = "NEEDS_FOLLOW_UP"
    no_action_possible = "NO_ACTION_POSSIBLE"
    other = "OTHER"


class RiskLevel(StrEnum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    critical = "CRITICAL"


class Urgency(StrEnum):
    unknown = "UNKNOWN"
    not_sure = "NOT_SURE"
    routine = "ROUTINE"
    now = "NOW"
    today = "TODAY"
    this_week = "THIS_WEEK"
    within_24_hours = "WITHIN_24_HOURS"


class ReportCategory(StrEnum):
    land_conflict = "LAND_CONFLICT"
    water_or_resource_conflict = "WATER_OR_RESOURCE_CONFLICT"
    hate_speech_or_incitement = "HATE_SPEECH_OR_INCITEMENT"
    armed_group_movement = "ARMED_GROUP_MOVEMENT"
    election_intimidation = "ELECTION_INTIMIDATION"
    displacement_risk = "DISPLACEMENT_RISK"
    gbv_or_protection_risk = "GBV_OR_PROTECTION_RISK"
    police_or_security_abuse = "POLICE_OR_SECURITY_ABUSE"
    aid_diversion = "AID_DIVERSION"
    public_service_failure = "PUBLIC_SERVICE_FAILURE"
    resource_exploitation = "RESOURCE_EXPLOITATION"
    community_rumor = "COMMUNITY_RUMOR"
    other = "OTHER"
    not_sure = "NOT_SURE"


class ApproximateLocation(ApiModel):
    country: str | None = Field(default=None, max_length=120)
    admin_level_1: str | None = Field(
        default=None, validation_alias=AliasChoices("admin_level_1", "adminLevel1"), max_length=160
    )
    admin_level_2: str | None = Field(
        default=None, validation_alias=AliasChoices("admin_level_2", "adminLevel2"), max_length=160
    )
    nearest_area: str | None = Field(
        default=None, validation_alias=AliasChoices("nearest_area", "nearestArea", "area"), max_length=200
    )
    landmark: str | None = Field(default=None, max_length=240)
    location_precision: str = Field(
        default="COARSE",
        validation_alias=AliasChoices("location_precision", "locationPrecision", "precision"),
        max_length=80,
    )
    raw_location_text: str | None = Field(
        default=None,
        validation_alias=AliasChoices("raw_location_text", "rawLocationText", "areaDescription"),
        max_length=500,
    )


class ConsentInput(ApiModel):
    safety_notice_accepted: bool = True
    data_use_accepted: bool = True
    anonymous_submission_accepted: bool = True
    share_with_mediator: bool = True

    @model_validator(mode="after")
    def validate_safety_notice(self) -> "ConsentInput":
        if not self.safety_notice_accepted:
            raise ValueError("Safety notice must be accepted")
        return self


class ReportCreateRequest(ApiModel):
    text: str = Field(min_length=10, max_length=5000)
    language: str = Field(default="English", min_length=2, max_length=80)
    channel: Literal["pwa", "sms_simulated", "whatsapp_simulated"] = "pwa"
    category_hint: ReportCategory = Field(
        default=ReportCategory.not_sure, validation_alias=AliasChoices("category_hint", "categoryHint")
    )
    timeframe: Urgency = Field(
        default=Urgency.unknown, validation_alias=AliasChoices("timeframe", "urgencyHint", "urgency_hint")
    )
    immediate_danger: bool = False
    location: ApproximateLocation = Field(default_factory=ApproximateLocation)
    consent: ConsentInput = Field(default_factory=ConsentInput)


class ReportCreateResponse(ApiModel):
    report_id: str
    tracking_code: str
    status: ReportStatus
    safe_status: str
    message: str


class AuthLoginRequest(ApiModel):
    username: str = Field(validation_alias=AliasChoices("username", "email"), min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class UserSummary(ApiModel):
    user_id: str
    name: str
    role: UserRole
    organization_id: str | None = None
    active: bool = True
    email: str | None = None


class AuthTokenResponse(ApiModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    role: UserRole
    user: UserSummary


class AuthenticatedUser(ApiModel):
    id: str
    username: str
    role: UserRole
    organization_id: str | None = None


class IntakeResult(ApiModel):
    category: ReportCategory = ReportCategory.not_sure
    urgency: Urgency = Urgency.not_sure
    risk_level: RiskLevel = RiskLevel.medium
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    redacted_text: str
    translated_text: str
    summary: str
    recommended_mediator_action: str
    safety_warning: str
    embedding: list[float] = Field(default_factory=list)


class AiApiResult(ApiModel):
    category: ReportCategory
    risk_level: RiskLevel
    urgency: Urgency
    summary: str
    redacted_text: str
    translated_text: str
    recommended_mediator_action: str
    confidence: float
    needs_human_review: bool = True
    safety_warnings: list[str] = Field(default_factory=list)


class ReportDocument(ApiModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="reportId")
    public_tracking_code: str = Field(alias="trackingCode")
    submitted_at: datetime
    channel: str
    language: str
    raw_text_encrypted: str
    redacted_text: str | None = None
    translated_text: str | None = None
    summary: str | None = None
    approximate_location: ApproximateLocation
    raw_location_encrypted: str | None = None
    location_precision: str = "coarse"
    category: ReportCategory = ReportCategory.not_sure
    urgency: Urgency = Urgency.not_sure
    risk_level: RiskLevel = RiskLevel.medium
    confidence_score: float = 0.0
    reporter_anonymous: bool = True
    consent_version: str = "2026-05-local"
    status: ReportStatus = ReportStatus.new
    cluster_id: str | None = None
    embedding: list[float] | None = Field(default=None, exclude=True)
    ai_recommended_mediator_action: str | None = None
    ai_safety_warnings: list[str] = Field(default_factory=list)
    needs_human_review: bool | None = None
    created_at: datetime
    updated_at: datetime


class VerificationRequest(ApiModel):
    decision: VerificationDecision
    notes: str = Field(default="", max_length=2000)
    confidence: float | str | None = None
    adjusted_category: ReportCategory | None = None
    adjusted_risk_level: RiskLevel | None = None
    adjusted_location: ApproximateLocation | None = None


class VerificationDocument(ApiModel):
    id: str
    report_id: str | None = None
    cluster_id: str | None = None
    verifier_id: str
    decision: VerificationDecision
    notes: str
    confidence: float | None = None
    adjusted_category: ReportCategory | None = None
    adjusted_risk_level: RiskLevel | None = None
    adjusted_location: ApproximateLocation | None = None
    created_at: datetime


class SignalClusterDocument(ApiModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="clusterId")
    title: str
    category: ReportCategory
    region: str
    risk_level: RiskLevel
    summary: str
    report_count: int
    report_ids: list[str]
    first_seen_at: datetime
    last_seen_at: datetime
    confidence_score: float
    status: ClusterStatus
    created_at: datetime
    updated_at: datetime


class ReportListResponse(ApiModel):
    items: list[ReportDocument]
    total: int


class ReportProcessResponse(ApiModel):
    report_id: str
    status: ReportStatus
    ai: AiApiResult
    cluster_ids: list[str] = Field(default_factory=list)


class ClusterListResponse(ApiModel):
    items: list[SignalClusterDocument]
    total: int


class EscalationCreateRequest(ApiModel):
    assigned_to: str = Field(
        default="mediator@sautirelay.dev",
        validation_alias=AliasChoices("assigned_to", "assignedTo", "mediatorId"),
        min_length=3,
        max_length=200,
    )
    assigned_organization: str = Field(
        default="Local mediation network",
        validation_alias=AliasChoices("assigned_organization", "assignedOrganization", "mediatorOrganizationId"),
        min_length=2,
        max_length=200,
    )
    urgency: Urgency = Urgency.within_24_hours
    safety_note: str = Field(default="Do not disclose reporter details.", max_length=1000)
    follow_up_due_at: datetime | None = None


class EscalationDocument(ApiModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="escalationId")
    cluster_id: str | None = None
    report_id: str | None = None
    assigned_to: str
    assigned_organization: str
    action_brief: str
    safety_note: str
    urgency: Urgency
    status: EscalationStatus
    assigned_role: Literal["mediator"] = "mediator"
    sent_at: datetime
    accepted_at: datetime | None = None
    resolved_at: datetime | None = None
    follow_up_due_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OutcomeCreateRequest(ApiModel):
    outcome_type: OutcomeType
    notes: str = Field(min_length=1, max_length=2500)
    deescalated: bool = False
    follow_up_required: bool = False
    safety_concerns: str | None = Field(default=None, max_length=1000)
    next_review_at: datetime | None = None


class OutcomeDocument(ApiModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="outcomeId")
    escalation_id: str
    outcome_type: OutcomeType
    notes: str
    deescalated: bool
    follow_up_required: bool
    recorded_by: str
    created_at: datetime


class AuditLogDocument(ApiModel):
    id: str
    actor_id: str | None = None
    action: str
    entity_type: str
    entity_id: str
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime


class MetricCount(ApiModel):
    label: str
    count: int


class DashboardMetrics(ApiModel):
    total_reports: int
    reports_by_status: dict[str, int]
    reports_by_category: list[MetricCount]
    risk_levels: list[MetricCount]
    active_clusters: int
    escalated_signals: int
    resolved_signals: int
    clusters_total: int
    escalations_total: int
    outcomes_total: int
    high_risk_reports: int
    average_verification_time_seconds: float | None = None


class SafeStatusResponse(ApiModel):
    tracking_code: str
    status: str


class StatusResponse(ApiModel):
    status: Literal["ok"]
    service: Literal["sautirelay"]


class ErrorResponse(ApiModel):
    code: str
    message: str
