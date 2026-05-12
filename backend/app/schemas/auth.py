"""Authentication and local user schemas."""

from pydantic import Field

from .common import ApiModel, UserRole


class LoginRequest(ApiModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)


class UserSummary(ApiModel):
    user_id: str = Field(alias="userId")
    name: str
    role: UserRole
    organization_id: str = Field(alias="organizationId")
    active: bool
    email: str | None = None


class AuthTokenResponse(ApiModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    expires_in: int = Field(alias="expiresIn", ge=1)
    user: UserSummary
