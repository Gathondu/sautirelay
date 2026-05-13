from typing import Annotated

from backend.app.core.models import AuthenticatedUser, DashboardMetrics
from backend.app.routers.dependencies import get_current_user, get_workflow_service
from backend.app.services.workflow import WorkflowService
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> DashboardMetrics:
    _ = user
    return await workflow.dashboard_metrics()
