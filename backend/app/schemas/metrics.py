"""Privacy-safe aggregate metric schemas."""

from pydantic import Field

from .common import ApiModel, MetricCount


class DashboardMetricsResponse(ApiModel):
    reports_by_category: list[MetricCount] = Field(alias="reportsByCategory")
    reports_by_region: list[MetricCount] = Field(alias="reportsByRegion")
    risk_levels: list[MetricCount] = Field(alias="riskLevels")
    active_clusters: int = Field(alias="activeClusters", ge=0)
    escalated_signals: int = Field(alias="escalatedSignals", ge=0)
    resolved_signals: int = Field(alias="resolvedSignals", ge=0)
    average_verification_hours: float = Field(alias="averageVerificationHours", ge=0)
    average_mediator_response_hours: float = Field(alias="averageMediatorResponseHours", ge=0)
