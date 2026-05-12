"""Signal cluster schemas for verifier review."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from .common import ApiModel, AuditEvent, ReportCategory, RiskLevel


class ClusterStatus(str, Enum):
    NEW = "NEW"
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    ESCALATED = "ESCALATED"
    DISMISSED = "DISMISSED"
    ARCHIVED = "ARCHIVED"
    RESOLVED = "RESOLVED"


class ClusterSummary(ApiModel):
    cluster_id: str = Field(alias="clusterId")
    title: str
    category: ReportCategory
    region: str
    risk_level: RiskLevel = Field(alias="riskLevel")
    summary: str
    report_count: int = Field(alias="reportCount", ge=1)
    first_seen_at: datetime = Field(alias="firstSeenAt")
    last_seen_at: datetime = Field(alias="lastSeenAt")
    confidence: float = Field(ge=0, le=1)
    status: ClusterStatus


class ClusterDetail(ClusterSummary):
    report_ids: list[str] = Field(default_factory=list, alias="reportIds")
    recommended_mediator_action: str = Field(alias="recommendedMediatorAction")
    safety_warnings: list[str] = Field(default_factory=list, alias="safetyWarnings")
    audit_events: list[AuditEvent] = Field(default_factory=list, alias="auditEvents")


class ClusterListResponse(ApiModel):
    items: list[ClusterSummary]
    total: int = Field(ge=0)
