from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.app.core.models import (
    AiApiResult,
    AuthenticatedUser,
    EscalationDocument,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportDocument,
    ReportListResponse,
    ReportProcessResponse,
    SafeStatusResponse,
    VerificationRequest,
)
from backend.app.routers.dependencies import get_workflow_service, require_verifier
from backend.app.services.workflow import WorkflowService

router = APIRouter(tags=["reports"])


@router.post("/reports", response_model=ReportCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportCreateRequest,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
) -> ReportCreateResponse:
    return await workflow.submit_report(request)


@router.get("/reports/status/{trackingCode}", response_model=SafeStatusResponse)
async def get_report_status(
    trackingCode: str,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
) -> SafeStatusResponse:
    return await workflow.get_safe_status(trackingCode)


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> ReportListResponse:
    _ = verifier
    reports = await workflow.list_reports()
    return ReportListResponse(items=reports, total=len(reports))


@router.get("/reports/{reportId}", response_model=ReportDocument)
async def get_report(
    reportId: str,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> ReportDocument:
    _ = verifier
    return await workflow.get_report(reportId)


@router.post("/reports/{reportId}/process", response_model=ReportProcessResponse)
async def process_report(
    reportId: str,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> ReportProcessResponse:
    report = await workflow.process_report(reportId, verifier)
    ai = AiApiResult(
        category=report.category,
        risk_level=report.risk_level,
        urgency=report.urgency,
        summary=report.summary or "",
        redacted_text=report.redacted_text or "",
        translated_text=report.translated_text or "",
        recommended_mediator_action="Review with trusted local mediators before any public action.",
        confidence=report.confidence_score,
        safety_warnings=["Do not disclose reporter details."],
    )
    return ReportProcessResponse(
        report_id=report.id,
        status=report.status,
        ai=ai,
        cluster_ids=[report.cluster_id] if report.cluster_id is not None else [],
    )


@router.post("/reports/{reportId}/verify", response_model=ReportDocument | EscalationDocument)
async def verify_report(
    reportId: str,
    request: VerificationRequest,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> ReportDocument | EscalationDocument:
    return await workflow.verify_report(reportId, request, verifier)
