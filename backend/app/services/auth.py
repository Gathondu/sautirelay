import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, TypedDict

from fastapi import HTTPException, status

from backend.app.core.config import Settings
from backend.app.core.models import AuthenticatedUser, UserRole


class TokenClaims(TypedDict):
    sub: str
    username: str
    role: str
    iss: str
    exp: int


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self._settings: Settings = settings
        self._users: Mapping[str, AuthenticatedUser] = {
            settings.verifier_username: AuthenticatedUser(
                id="user_verifier_local",
                username=settings.verifier_username,
                role=UserRole.verifier,
                organization_id="org_local_peace_committee",
            ),
            settings.mediator_username: AuthenticatedUser(
                id="user_mediator_local",
                username=settings.mediator_username,
                role=UserRole.mediator,
                organization_id="org_local_mediation_network",
            ),
        }
        self._passwords: dict[str, str] = {
            settings.verifier_username: settings.verifier_password,
            settings.mediator_username: settings.mediator_password,
        }

    def authenticate(self, username: str, password: str) -> AuthenticatedUser:
        user = self._users.get(username)
        expected_password = self._passwords.get(username)
        if user is None or expected_password is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not hmac.compare_digest(password, expected_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user

    def create_access_token(self, user: AuthenticatedUser) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._settings.jwt_ttl_seconds)
        claims: TokenClaims = {
            "sub": user.id,
            "username": user.username,
            "role": str(user.role),
            "iss": self._settings.jwt_issuer,
            "exp": int(expires_at.timestamp()),
        }
        return self._encode_jwt(claims)

    def verify_access_token(self, token: str) -> AuthenticatedUser:
        claims = self._decode_jwt(token)
        expires_at = datetime.fromtimestamp(claims["exp"], timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        if claims["iss"] != self._settings.jwt_issuer:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
        user = self._users.get(claims["username"])
        if user is None or user.id != claims["sub"] or str(user.role) != claims["role"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
        return user

    def require_role(self, user: AuthenticatedUser, role: UserRole) -> AuthenticatedUser:
        if user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{str(role)} role required")
        return user

    def _encode_jwt(self, claims: TokenClaims) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        header_segment = self._b64_json(header)
        claims_segment = self._b64_json(claims)
        signature = self._sign(f"{header_segment}.{claims_segment}")
        return f"{header_segment}.{claims_segment}.{signature}"

    def _decode_jwt(self, token: str) -> TokenClaims:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        signed = f"{parts[0]}.{parts[1]}"
        expected_signature = self._sign(signed)
        if not hmac.compare_digest(parts[2], expected_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")
        payload = json.loads(self._b64_decode(parts[1]).decode("utf-8"))
        if not self._has_required_claims(payload):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
        return TokenClaims(
            sub=payload["sub"],
            username=payload["username"],
            role=payload["role"],
            iss=payload["iss"],
            exp=payload["exp"],
        )

    def _sign(self, value: str) -> str:
        digest = hmac.new(
            self._settings.jwt_secret.encode("utf-8"),
            value.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return self._b64_bytes(digest)

    @staticmethod
    def _b64_json(value: Mapping[str, Any]) -> str:
        encoded = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return AuthService._b64_bytes(encoded)

    @staticmethod
    def _b64_bytes(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")

    @staticmethod
    def _b64_decode(value: str) -> bytes:
        padded = value + "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(padded)

    @staticmethod
    def _has_required_claims(payload: object) -> bool:
        if not isinstance(payload, dict):
            return False
        return all(key in payload for key in ("sub", "username", "role", "iss", "exp"))
