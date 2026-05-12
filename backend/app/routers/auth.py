from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.core.config import Settings, get_settings
from backend.app.core.models import AuthLoginRequest, AuthTokenResponse, UserSummary
from backend.app.routers.dependencies import get_auth_service
from backend.app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    request: AuthLoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthTokenResponse:
    user = auth_service.authenticate(request.username, request.password)
    token = auth_service.create_access_token(user)
    return AuthTokenResponse(
        access_token=token,
        expires_in=settings.jwt_ttl_seconds,
        role=user.role,
        user=UserSummary(
            user_id=user.id,
            name=user.username,
            role=user.role,
            organization_id=user.organization_id,
            email=user.username,
        ),
    )
