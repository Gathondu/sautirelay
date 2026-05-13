import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_CORS_ALLOW_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)
DEFAULT_CORS_ALLOW_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
DEFAULT_CORS_ALLOW_HEADERS = ("Authorization", "Content-Type")
REPO_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(REPO_ROOT / ".env", override=False)


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
    openai_api_key: str | None
    openai_base_url: str | None
    openai_model: str
    openai_max_output_tokens: int
    embedding_model: str
    embedding_dimensions: int | None
    embedding_input_type: str | None
    embedding_extra_body: dict[str, object]
    embedding_extra_headers: dict[str, str]
    cors_allow_origins: tuple[str, ...]
    cors_allow_credentials: bool
    cors_allow_methods: tuple[str, ...]
    cors_allow_headers: tuple[str, ...]
    demo_seed_enabled: bool
    demo_seed_with_ai: bool
    ai_allow_deterministic_fallback: bool
    local_data_dir: Path


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


def _optional_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _optional_int_env(name: str) -> int | None:
    value = _optional_env(name)
    if value is None:
        return None
    return int(value)


def _json_object_env(name: str) -> dict[str, object]:
    value = _optional_env(name)
    if value is None:
        return {}

    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object.")
    return parsed


def _string_json_object_env(name: str) -> dict[str, str]:
    return {key: str(value) for key, value in _json_object_env(name).items()}


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name="SautiRelay",
        environment=os.getenv("ENV", "dev"),
        jwt_secret=os.getenv("JWT_SECRET", "dev-only-change-me"),
        jwt_issuer=os.getenv("JWT_ISSUER", "sautirelay-dev"),
        jwt_ttl_seconds=int(os.getenv("JWT_TTL_SECONDS", "3600")),
        verifier_username=os.getenv("VERIFIER_USERNAME", "verifier@sautirelay.dev"),
        verifier_password=os.getenv("VERIFIER_PASSWORD", "verifier-dev-pass"),
        mediator_username=os.getenv("MEDIATOR_USERNAME", "mediator@sautirelay.dev"),
        mediator_password=os.getenv("MEDIATOR_PASSWORD", "mediator-dev-pass"),
        openai_api_key=_optional_env("OPENAI_API_KEY"),
        openai_base_url=_optional_env("OPENAI_BASE_URL"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.5"),
        openai_max_output_tokens=int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "1200")),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        embedding_dimensions=_optional_int_env("EMBEDDING_DIMENSIONS"),
        embedding_input_type=_optional_env("EMBEDDING_INPUT_TYPE"),
        embedding_extra_body=_json_object_env("EMBEDDING_EXTRA_BODY"),
        embedding_extra_headers=_string_json_object_env("EMBEDDING_EXTRA_HEADERS"),
        cors_allow_origins=_parse_csv_setting(
            os.getenv("CORS_ALLOW_ORIGINS"),
            DEFAULT_CORS_ALLOW_ORIGINS,
        ),
        cors_allow_credentials=_parse_bool_setting(
            os.getenv("CORS_ALLOW_CREDENTIALS"),
            False,
        ),
        cors_allow_methods=_parse_csv_setting(
            os.getenv("CORS_ALLOW_METHODS"),
            DEFAULT_CORS_ALLOW_METHODS,
        ),
        cors_allow_headers=_parse_csv_setting(
            os.getenv("CORS_ALLOW_HEADERS"),
            DEFAULT_CORS_ALLOW_HEADERS,
        ),
        demo_seed_enabled=_demo_seed_enabled_default(),
        demo_seed_with_ai=_parse_bool_setting(os.getenv("DEMO_SEED_WITH_AI"), False),
        ai_allow_deterministic_fallback=_parse_bool_setting(
            os.getenv("AI_ALLOW_DETERMINISTIC_FALLBACK"),
            False,
        ),
        local_data_dir=Path(os.getenv("LOCAL_DATA_DIR", ".local-data")),
    )


def _demo_seed_enabled_default() -> bool:
    raw_demo = os.getenv("DEMO_SEED_ENABLED")
    if raw_demo is not None:
        return _parse_bool_setting(raw_demo, False)
    env = os.getenv("ENV", "dev").strip().lower()
    if env == "test":
        return False
    return env == "dev"
