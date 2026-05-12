import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the backend."""

    app_name: str
    environment: str
    jwt_secret: str
    jwt_issuer: str
    jwt_ttl_seconds: int
    verifier_username: str
    verifier_password: str
    mediator_username: str
    mediator_password: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name="SautiRelay",
        environment=os.getenv("SAUTIRELAY_ENV", "dev"),
        jwt_secret=os.getenv("SAUTIRELAY_JWT_SECRET", "dev-only-change-me"),
        jwt_issuer=os.getenv("SAUTIRELAY_JWT_ISSUER", "sautirelay-dev"),
        jwt_ttl_seconds=int(os.getenv("SAUTIRELAY_JWT_TTL_SECONDS", "3600")),
        verifier_username=os.getenv("SAUTIRELAY_VERIFIER_USERNAME", "verifier@sautirelay.dev"),
        verifier_password=os.getenv("SAUTIRELAY_VERIFIER_PASSWORD", "verifier-dev-pass"),
        mediator_username=os.getenv("SAUTIRELAY_MEDIATOR_USERNAME", "mediator@sautirelay.dev"),
        mediator_password=os.getenv("SAUTIRELAY_MEDIATOR_PASSWORD", "mediator-dev-pass"),
    )
