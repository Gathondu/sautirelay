from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.app.core.models import AuthenticatedUser, EscalationDocument, OutcomeCreateRequest, OutcomeDocument
from backend.app.routers.dependencies import get_workflow_service, require_mediator
from backend.app.services.workflow import WorkflowService

router = APIRouter(prefix="/escalations", tags=["escalations"])


@router.get("", response_model=list[EscalationDocument])
async def list_escalations(
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    mediator: Annotated[AuthenticatedUser, Depends(require_mediator)],
) -> list[EscalationDocument]:
    return await workflow.list_escalations(mediator)


@router.get("/{escalationId}", response_model=EscalationDocument)
async def get_escalation(
    escalationId: str,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    mediator: Annotated[AuthenticatedUser, Depends(require_mediator)],
) -> EscalationDocument:
    return await workflow.get_escalation(escalationId, mediator)


@router.post("/{escalationId}/accept", response_model=EscalationDocument)
async def accept_escalation(
    escalationId: str,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    mediator: Annotated[AuthenticatedUser, Depends(require_mediator)],
) -> EscalationDocument:
    return await workflow.accept_escalation(escalationId, mediator)


@router.post("/{escalationId}/outcome", response_model=OutcomeDocument, status_code=status.HTTP_201_CREATED)
async def record_outcome(
    escalationId: str,
    request: OutcomeCreateRequest,
    workflow: Annotated[WorkflowService, Depends(get_workflow_service)],
    mediator: Annotated[AuthenticatedUser, Depends(require_mediator)],
) -> OutcomeDocument:
    return await workflow.record_outcome(escalationId, request, mediator)
