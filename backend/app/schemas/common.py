"""Shared schema primitives for SautiRelay."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    """Base model that accepts Python field names and emits API aliases."""

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)


class UserRole(str, Enum):
    VERIFIER = "VERIFIER"
    MEDIATOR = "MEDIATOR"
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"


class Channel(str, Enum):
    PWA = "pwa"
    SMS_SIMULATED = "sms_simulated"
    CHAT_SIMULATED = "chat_simulated"


class ReportCategory(str, Enum):
    LAND_CONFLICT = "LAND_CONFLICT"
    WATER_OR_RESOURCE_CONFLICT = "WATER_OR_RESOURCE_CONFLICT"
    HATE_SPEECH_OR_INCITEMENT = "HATE_SPEECH_OR_INCITEMENT"
    ARMED_GROUP_MOVEMENT = "ARMED_GROUP_MOVEMENT"
    ELECTION_INTIMIDATION = "ELECTION_INTIMIDATION"
    DISPLACEMENT_RISK = "DISPLACEMENT_RISK"
    GBV_OR_PROTECTION_RISK = "GBV_OR_PROTECTION_RISK"
    POLICE_OR_SECURITY_ABUSE = "POLICE_OR_SECURITY_ABUSE"
    AID_DIVERSION = "AID_DIVERSION"
    PUBLIC_SERVICE_FAILURE = "PUBLIC_SERVICE_FAILURE"
    RESOURCE_EXPLOITATION = "RESOURCE_EXPLOITATION"
    COMMUNITY_RUMOR = "COMMUNITY_RUMOR"
    OTHER = "OTHER"
    NOT_SURE = "NOT_SURE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Urgency(str, Enum):
    UNKNOWN = "UNKNOWN"
    ROUTINE = "ROUTINE"
    THIS_WEEK = "THIS_WEEK"
    WITHIN_24_HOURS = "WITHIN_24_HOURS"
    IMMEDIATE = "IMMEDIATE"


class LocationPrecision(str, Enum):
    NONE = "NONE"
    COARSE = "COARSE"
    FIVE_TO_TEN_KM = "FIVE_TO_TEN_KM"
    EXACT_IF_SAFE = "EXACT_IF_SAFE"


class StatusResponse(ApiModel):
    status: str = Field(default="ok")
    service: str = Field(default="sautirelay")
    version: str = Field(default="0.2.0")


class ErrorResponse(ApiModel):
    code: str
    message: str
    field: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class LocationVisibility(ApiModel):
    internal_area: str = Field(alias="internalArea")
    mediator_area: str = Field(alias="mediatorArea")
    analytics_area: str = Field(alias="analyticsArea")
    public_area: str = Field(alias="publicArea")
    precision: LocationPrecision


class MetricCount(ApiModel):
    label: str
    count: int = Field(ge=0)


class AuditEvent(ApiModel):
    audit_id: str = Field(alias="auditId")
    action: str
    entity_type: str = Field(alias="entityType")
    entity_id: str = Field(alias="entityId")
    created_at: datetime = Field(alias="createdAt")
    actor_id: str | None = Field(default=None, alias="actorId")
    metadata: dict[str, object] = Field(default_factory=dict)
