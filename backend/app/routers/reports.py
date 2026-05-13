from typing import Annotated

from backend.app.core.models import (
    AuthenticatedUser,
    EscalationDocument,
    QueuedOperationResponse,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportDocument,
    ReportListResponse,
    SafeStatusResponse,
    VerificationRequest,
)
from backend.app.routers.dependencies import get_workflow_service, require_verifier
from backend.app.services.workflow import WorkflowService
from fastapi import APIRouter, BackgroundTasks, Depends, status

router = APIRouter(tags=["reports"])


@router.post("/reports", response_model=ReportCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportCreateRequest,
    background_tasks: BackgroundTasks,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
) -> ReportCreateResponse:
    report = await workflow.submit_report(request)
    background_tasks.add_task(workflow.process_report_in_background, report.id, None)
    return workflow.build_report_create_response(report)


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


@router.post(
    "/reports/{reportId}/process",
    response_model=QueuedOperationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_report(
    reportId: str,
    background_tasks: BackgroundTasks,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> QueuedOperationResponse:
    report = await workflow.get_report(reportId)
    if report.status in {"NEW", "PROCESSING"}:
        background_tasks.add_task(workflow.process_report_in_background, report.id, verifier.id)
        return QueuedOperationResponse(
            entity_id=report.id,
            status="PROCESSING",
            message="AI intake has started in the background.",
        )

    return QueuedOperationResponse(
        entity_id=report.id,
        status=report.status,
        message=f"Report is already {report.status}.",
    )


@router.post("/reports/{reportId}/verify", response_model=ReportDocument | EscalationDocument)
async def verify_report(
    reportId: str,
    request: VerificationRequest,
    background_tasks: BackgroundTasks,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> ReportDocument | EscalationDocument:
    result = await workflow.verify_report(reportId, request, verifier)
    if isinstance(result, EscalationDocument) and result.status == "PREPARING_BRIEF" and result.report_id:
        background_tasks.add_task(
            workflow.finalize_report_escalation_brief,
            result.id,
            result.report_id,
            verifier.id,
        )
    return result
