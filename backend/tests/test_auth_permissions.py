from __future__ import annotations

from conftest import (
    MEDIATOR_CREDENTIALS,
    VERIFIER_CREDENTIALS,
    assert_json_response,
    auth_header,
    login,
    mediator_headers,
    verifier_headers,
)
from fastapi.testclient import TestClient


def test_seeded_verifier_can_login(client: TestClient) -> None:
    token = login(client, VERIFIER_CREDENTIALS)
    assert token.count(".") == 2


def test_seeded_mediator_can_login(client: TestClient) -> None:
    token = login(client, MEDIATOR_CREDENTIALS)
    assert token.count(".") == 2


def test_invalid_credentials_fail_without_token(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "verifier@sautirelay.dev", "password": "wrong-password"},
    )
    payload = assert_json_response(response, 401)
    assert "accessToken" not in payload
    assert "access_token" not in payload


def test_verifier_endpoints_reject_missing_token(client: TestClient) -> None:
    response = client.get("/reports")
    assert response.status_code in {401, 403}, response.text


def test_mediator_endpoints_reject_missing_token(client: TestClient) -> None:
    response = client.get("/escalations")
    assert response.status_code in {401, 403}, response.text


def test_verifier_queue_rejects_mediator_role(client: TestClient) -> None:
    response = client.get("/reports", headers=mediator_headers(client))
    assert response.status_code == 403, response.text


def test_mediator_queue_rejects_verifier_role(client: TestClient) -> None:
    response = client.get("/escalations", headers=verifier_headers(client))
    assert response.status_code == 403, response.text


def test_protected_endpoints_reject_tampered_token(client: TestClient) -> None:
    verifier_token = login(client, VERIFIER_CREDENTIALS)
    response = client.get("/reports", headers=auth_header(f"{verifier_token}tampered"))
    assert response.status_code in {401, 403}, response.text
