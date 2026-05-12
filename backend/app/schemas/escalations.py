"""Mediator escalation and outcome schemas."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from .common import ApiModel, Urgency


class EscalationStatus(str, Enum):
    PENDING_ACCEPTANCE = "PENDING_ACCEPTANCE"
    ACCEPTED = "ACCEPTED"
    ACTION_TAKEN = "ACTION_TAKEN"
    FOLLOW_UP_NEEDED = "FOLLOW_UP_NEEDED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class OutcomeType(str, Enum):
    DIALOGUE_HELD = "DIALOGUE_HELD"
    REFERRED_TO_PARTNER = "REFERRED_TO_PARTNER"
    FALSE_ALARM = "FALSE_ALARM"
    RISK_REDUCED = "RISK_REDUCED"
    VIOLENCE_OCCURRED = "VIOLENCE_OCCURRED"
    NEEDS_FOLLOW_UP = "NEEDS_FOLLOW_UP"
    NO_ACTION_POSSIBLE = "NO_ACTION_POSSIBLE"
    OTHER = "OTHER"


class EscalationCreateRequest(ApiModel):
    mediator_id: str = Field(alias="mediatorId")
    action_brief: str = Field(alias="actionBrief", min_length=20, max_length=5000)
    safety_note: str = Field(alias="safetyNote", min_length=1, max_length=2000)
    urgency: Urgency
    follow_up_due_at: datetime = Field(alias="followUpDueAt")
    mediator_organization_id: str | None = Field(default=None, alias="mediatorOrganizationId")


class EscalationSummary(ApiModel):
    escalation_id: str = Field(alias="escalationId")
    cluster_id: str = Field(alias="clusterId")
    mediator_id: str = Field(alias="mediatorId")
    action_brief: str = Field(alias="actionBrief")
    urgency: Urgency
    status: EscalationStatus
    sent_at: datetime = Field(alias="sentAt")
    report_id: str | None = Field(default=None, alias="reportId")


class EscalationDetail(EscalationSummary):
    safety_note: str = Field(alias="safetyNote")
    approximate_area: str = Field(alias="approximateArea")
    recommended_actions: list[str] = Field(default_factory=list, alias="recommendedActions")
    field_notes: list[str] = Field(default_factory=list, alias="fieldNotes")
    mediator_organization_id: str | None = Field(default=None, alias="mediatorOrganizationId")
    accepted_at: datetime | None = Field(default=None, alias="acceptedAt")
    resolved_at: datetime | None = Field(default=None, alias="resolvedAt")
    follow_up_due_at: datetime | None = Field(default=None, alias="followUpDueAt")


class EscalationListResponse(ApiModel):
    items: list[EscalationSummary]
    total: int = Field(ge=0)


class OutcomeCreateRequest(ApiModel):
    outcome_type: OutcomeType = Field(alias="outcomeType")
    notes: str = Field(min_length=1, max_length=4000)
    deescalated: bool
    follow_up_required: bool = Field(alias="followUpRequired")
    safety_concerns: str | None = Field(default=None, alias="safetyConcerns", max_length=2000)
    next_review_at: datetime | None = Field(default=None, alias="nextReviewAt")


class OutcomeDetail(ApiModel):
    outcome_id: str = Field(alias="outcomeId")
    escalation_id: str = Field(alias="escalationId")
    outcome_type: OutcomeType = Field(alias="outcomeType")
    notes: str
    deescalated: bool
    follow_up_required: bool = Field(alias="followUpRequired")
    recorded_by: str = Field(alias="recordedBy")
    created_at: datetime = Field(alias="createdAt")
    safety_concerns: str | None = Field(default=None, alias="safetyConcerns")
    next_review_at: datetime | None = Field(default=None, alias="nextReviewAt")
