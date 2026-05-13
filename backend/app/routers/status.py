from backend.app.core.models import StatusResponse
from fastapi import APIRouter

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    return StatusResponse(status="ok", service="sautirelay")
