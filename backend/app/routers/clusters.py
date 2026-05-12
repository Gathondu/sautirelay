from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from backend.app.core.models import (
    AuthenticatedUser,
    ClusterListResponse,
    EscalationCreateRequest,
    EscalationDocument,
    SignalClusterDocument,
    VerificationRequest,
)
from backend.app.routers.dependencies import get_workflow_service, require_verifier
from backend.app.services.workflow import WorkflowService

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=ClusterListResponse)
async def list_clusters(
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> ClusterListResponse:
    _ = verifier
    clusters = await workflow.list_clusters()
    return ClusterListResponse(items=clusters, total=len(clusters))


@router.get("/{clusterId}", response_model=SignalClusterDocument)
async def get_cluster(
    clusterId: str,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> SignalClusterDocument:
    _ = verifier
    return await workflow.get_cluster(clusterId)


@router.post("/{clusterId}/verify", response_model=SignalClusterDocument)
async def verify_cluster(
    clusterId: str,
    request: VerificationRequest,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> SignalClusterDocument:
    return await workflow.verify_cluster(clusterId, request, verifier)


@router.post("/{clusterId}/escalate", response_model=EscalationDocument, status_code=status.HTTP_201_CREATED)
async def escalate_cluster(
    clusterId: str,
    request: EscalationCreateRequest,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    verifier: Annotated[AuthenticatedUser, Depends(require_verifier)],
) -> EscalationDocument:
    return await workflow.escalate_cluster(clusterId, request, verifier)
