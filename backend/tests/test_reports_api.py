from __future__ import annotations

from typing import Any

from conftest import (
    aid_diversion_report,
    assert_json_response,
    mediator_headers,
    verifier_headers,
    water_conflict_report,
)
from fastapi.testclient import TestClient


def submit_report(client: TestClient, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client.post("/reports", json=payload or water_conflict_report())
    return assert_json_response(response, 201)


def test_anonymous_report_submission_returns_tracking_code_and_safe_status(client: TestClient) -> None:
    payload = submit_report(client)

    assert payload["reportId"]
    assert payload["trackingCode"].startswith("SR-")
    assert payload["status"] in {"NEW", "PROCESSING", "PENDING_REVIEW", "Received"}
    assert "rawText" not in payload
    assert "reporter" not in payload


def test_report_status_lookup_is_safe_for_anonymous_reporter(client: TestClient) -> None:
    created = submit_report(client)

    response = client.get(f"/reports/status/{created['trackingCode']}")
    payload = assert_json_response(response, 200)

    assert payload["trackingCode"] == created["trackingCode"]
    assert payload["status"] in {
        "Received",
        "Under review",
        "Verified",
        "Escalated to trusted mediator",
        "Closed",
        "Unable to verify",
    }
    forbidden_keys = {"rawText", "verifierNotes", "mediatorId", "actionBrief", "internalArea"}
    assert forbidden_keys.isdisjoint(payload)


def test_report_validation_rejects_missing_safety_consent(client: TestClient) -> None:
    payload = water_conflict_report()
    payload["consent"]["safetyNoticeAccepted"] = False

    response = client.post("/reports", json=payload)
    assert response.status_code == 422, response.text


def test_verifier_can_list_and_open_reports(client: TestClient) -> None:
    created = submit_report(client)
    headers = verifier_headers(client)

    queue_payload = assert_json_response(client.get("/reports", headers=headers), 200)
    reports = queue_payload.get("items", queue_payload.get("reports", []))
    assert any(report["reportId"] == created["reportId"] for report in reports)

    detail = assert_json_response(client.get(f"/reports/{created['reportId']}", headers=headers), 200)
    assert detail["reportId"] == created["reportId"]
    assert detail["status"] in {"NEW", "PROCESSING", "PENDING_REVIEW"}


def test_mediator_cannot_list_or_open_verifier_reports(client: TestClient) -> None:
    created = submit_report(client)
    headers = mediator_headers(client)

    assert client.get("/reports", headers=headers).status_code == 403
    assert client.get(f"/reports/{created['reportId']}", headers=headers).status_code == 403


def test_verifier_can_process_and_verify_report(client: TestClient) -> None:
    created = submit_report(client)
    headers = verifier_headers(client)

    processed = assert_json_response(
        client.post(f"/reports/{created['reportId']}/process", headers=headers),
        200,
    )
    assert processed["reportId"] == created["reportId"]
    assert processed["status"] in {"PENDING_REVIEW", "VERIFIED", "NEEDS_MORE_INFO"}
    assert processed["ai"]["needsHumanReview"] is True

    verified = assert_json_response(
        client.post(
            f"/reports/{created['reportId']}/verify",
            headers=headers,
            json={
                "decision": "VERIFIED",
                "notes": "Confirmed with local peace committee.",
                "confidence": "HIGH",
                "adjustedCategory": "WATER_OR_RESOURCE_CONFLICT",
                "adjustedRiskLevel": "HIGH",
            },
        ),
        200,
    )
    assert verified["status"] == "VERIFIED"


def test_unrelated_reports_remain_separate_in_verifier_queue(client: TestClient) -> None:
    first = submit_report(client, water_conflict_report())
    second = submit_report(client, aid_diversion_report())

    queue_payload = assert_json_response(client.get("/reports", headers=verifier_headers(client)), 200)
    reports = queue_payload.get("items", queue_payload.get("reports", []))
    report_by_id = {report["reportId"]: report for report in reports}

    assert first["reportId"] in report_by_id
    assert second["reportId"] in report_by_id
    assert report_by_id[first["reportId"]].get("clusterId") != report_by_id[second["reportId"]].get("clusterId")
