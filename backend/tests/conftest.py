from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


VERIFIER_CREDENTIALS = {
    "email": "verifier@sautirelay.dev",
    "password": "verifier-dev-pass",
}
MEDIATOR_CREDENTIALS = {
    "email": "mediator@sautirelay.dev",
    "password": "mediator-dev-pass",
}


@pytest.fixture(autouse=True)
def deterministic_local_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("SAUTIRELAY_ENV", "test")
    monkeypatch.setenv("SAUTIRELAY_JWT_SECRET", "test-only-secret")
    monkeypatch.setenv("SAUTIRELAY_OPENAI_MODEL", "test-model")
    monkeypatch.setenv("SAUTIRELAY_EMBEDDING_MODEL", "test-embedding-model")
    monkeypatch.setenv(
        "SAUTIRELAY_CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    from backend.app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    module = importlib.import_module("backend.app.main")
    module = importlib.reload(module)
    app = getattr(module, "app")

    reset_state = getattr(app.state, "reset_state", None)
    if callable(reset_state):
        reset_state()

    with TestClient(app) as test_client:
        yield test_client


def assert_json_response(response: Any, expected_status: int) -> dict[str, Any]:
    assert response.status_code == expected_status, response.text
    payload = response.json()
    assert isinstance(payload, dict)
    return payload


def login(client: TestClient, credentials: dict[str, str]) -> str:
    response = client.post("/auth/login", json=credentials)
    payload = assert_json_response(response, 200)
    token = payload.get("accessToken") or payload.get("access_token")
    assert isinstance(token, str) and token
    return token


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def verifier_headers(client: TestClient) -> dict[str, str]:
    return auth_header(login(client, VERIFIER_CREDENTIALS))


def mediator_headers(client: TestClient) -> dict[str, str]:
    return auth_header(login(client, MEDIATOR_CREDENTIALS))


def water_conflict_report(text: str | None = None) -> dict[str, Any]:
    return {
        "channel": "pwa",
        "language": "en",
        "categoryHint": "WATER_OR_RESOURCE_CONFLICT",
        "text": text
        or "There are rumors that youth from Village A may block herders at the water point tomorrow.",
        "timeframe": "WITHIN_24_HOURS",
        "immediateDanger": False,
        "location": {
            "country": "Mali",
            "adminLevel1": "Mopti",
            "area": "near the central water point",
            "landmark": "market borehole",
            "precision": "GENERAL_AREA_ONLY",
        },
        "consent": {
            "safetyNoticeAccepted": True,
            "anonymousSubmissionAccepted": True,
        },
    }


def aid_diversion_report() -> dict[str, Any]:
    return {
        "channel": "pwa",
        "language": "en",
        "categoryHint": "AID_DIVERSION",
        "text": "Some families in the camp were asked to pay before receiving aid supplies.",
        "timeframe": "THIS_WEEK",
        "immediateDanger": False,
        "location": {
            "country": "DRC",
            "adminLevel1": "North Kivu",
            "area": "Goma north",
            "precision": "GENERAL_AREA_ONLY",
        },
        "consent": {
            "safetyNoticeAccepted": True,
            "anonymousSubmissionAccepted": True,
        },
    }
