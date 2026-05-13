from __future__ import annotations

import importlib

import pytest
from backend.app.core.config import get_settings
from fastapi.testclient import TestClient


def test_cors_origins_are_loaded_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "SAUTIRELAY_CORS_ALLOW_ORIGINS",
        "http://localhost:5173, https://app.example.test ",
    )
    monkeypatch.setenv("SAUTIRELAY_CORS_ALLOW_CREDENTIALS", "true")
    monkeypatch.setenv("SAUTIRELAY_CORS_ALLOW_METHODS", "GET,POST")
    monkeypatch.setenv("SAUTIRELAY_CORS_ALLOW_HEADERS", "Authorization,X-Request-Id")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.cors_allow_origins == ("http://localhost:5173", "https://app.example.test")
    assert settings.cors_allow_credentials is True
    assert settings.cors_allow_methods == ("GET", "POST")
    assert settings.cors_allow_headers == ("Authorization", "X-Request-Id")


def test_cors_preflight_allows_configured_origin(client: TestClient) -> None:
    response = client.options(
        "/reports",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_preflight_rejects_unconfigured_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAUTIRELAY_CORS_ALLOW_ORIGINS", "https://app.example.test")
    get_settings.cache_clear()
    module = importlib.import_module("backend.app.main")
    module = importlib.reload(module)

    with TestClient(module.app) as client:
        response = client.options(
            "/reports",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert "access-control-allow-origin" not in response.headers
