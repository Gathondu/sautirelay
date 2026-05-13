import os
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_CORS_ALLOW_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)
DEFAULT_CORS_ALLOW_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
DEFAULT_CORS_ALLOW_HEADERS = ("Authorization", "Content-Type")


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
    cors_allow_origins: tuple[str, ...]
    cors_allow_credentials: bool
    cors_allow_methods: tuple[str, ...]
    cors_allow_headers: tuple[str, ...]


def _parse_csv_setting(raw_value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if raw_value is None:
        return default

    values = tuple(value.strip() for value in raw_value.split(",") if value.strip())
    return values or default


def _parse_bool_setting(raw_value: str | None, default: bool) -> bool:
    if raw_value is None:
        return default

    normalized_value = raw_value.strip().lower()
    if normalized_value in {"1", "true", "yes", "on"}:
        return True
    if normalized_value in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"Invalid boolean setting value: {raw_value!r}")


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
        cors_allow_origins=_parse_csv_setting(
            os.getenv("SAUTIRELAY_CORS_ALLOW_ORIGINS"),
            DEFAULT_CORS_ALLOW_ORIGINS,
        ),
        cors_allow_credentials=_parse_bool_setting(
            os.getenv("SAUTIRELAY_CORS_ALLOW_CREDENTIALS"),
            False,
        ),
        cors_allow_methods=_parse_csv_setting(
            os.getenv("SAUTIRELAY_CORS_ALLOW_METHODS"),
            DEFAULT_CORS_ALLOW_METHODS,
        ),
        cors_allow_headers=_parse_csv_setting(
            os.getenv("SAUTIRELAY_CORS_ALLOW_HEADERS"),
            DEFAULT_CORS_ALLOW_HEADERS,
        ),
    )
