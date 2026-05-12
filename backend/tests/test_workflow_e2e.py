from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from conftest import assert_json_response, mediator_headers, verifier_headers, water_conflict_report


def submit_report(client: TestClient, text: str | None = None) -> dict[str, Any]:
    response = client.post("/reports", json=water_conflict_report(text))
    return assert_json_response(response, 201)


def verify_report(client: TestClient, report_id: str, headers: dict[str, str]) -> dict[str, Any]:
    client.post(f"/reports/{report_id}/process", headers=headers)
    return assert_json_response(
        client.post(
            f"/reports/{report_id}/verify",
            headers=headers,
            json={
                "decision": "VERIFIED",
                "notes": "Verified through trusted local peace actor.",
                "confidence": "HIGH",
                "adjustedRiskLevel": "HIGH",
                "adjustedCategory": "WATER_OR_RESOURCE_CONFLICT",
            },
        ),
        200,
    )


def escalate_cluster_or_report(
    client: TestClient,
    report_id: str,
    verifier_auth: dict[str, str],
) -> dict[str, Any]:
    clusters_payload = assert_json_response(client.get("/clusters", headers=verifier_auth), 200)
    clusters = clusters_payload.get("items", clusters_payload.get("clusters", []))
    cluster = next(
        (
            candidate
            for candidate in clusters
            if report_id in candidate.get("reportIds", candidate.get("report_ids", []))
            or candidate.get("reportId") == report_id
        ),
        None,
    )

    if cluster is not None:
        cluster_id = cluster["clusterId"]
        client.post(
            f"/clusters/{cluster_id}/verify",
            headers=verifier_auth,
            json={"decision": "VERIFIED", "notes": "Related reports verified.", "confidence": "HIGH"},
        )
        response = client.post(
            f"/clusters/{cluster_id}/escalate",
            headers=verifier_auth,
            json={
                "mediatorId": "mediator-local-1",
                "urgency": "WITHIN_24_HOURS",
                "safetyNote": "Do not disclose reporter details or exact location.",
            },
        )
        return assert_json_response(response, 201)

    response = client.post(
        f"/reports/{report_id}/verify",
        headers=verifier_auth,
        json={
            "decision": "ESCALATE_IMMEDIATELY",
            "notes": "High-risk verified signal.",
            "confidence": "HIGH",
            "mediatorId": "mediator-local-1",
            "safetyNote": "Do not disclose reporter details or exact location.",
        },
    )
    return assert_json_response(response, 201)


def test_full_report_to_mediator_outcome_workflow(client: TestClient) -> None:
    created = submit_report(client)
    verifier_auth = verifier_headers(client)
    mediator_auth = mediator_headers(client)

    verified = verify_report(client, created["reportId"], verifier_auth)
    assert verified["status"] == "VERIFIED"

    escalation = escalate_cluster_or_report(client, created["reportId"], verifier_auth)
    escalation_id = escalation["escalationId"]
    assert escalation["status"] in {"ESCALATED", "PENDING_ACCEPTANCE"}
    assert "mediator" in escalation.get("assignedRole", "mediator").lower()

    detail = assert_json_response(client.get(f"/escalations/{escalation_id}", headers=mediator_auth), 200)
    assert detail["escalationId"] == escalation_id
    assert "actionBrief" in detail
    assert "rawText" not in detail
    assert "exact" not in str(detail).lower()

    accepted = assert_json_response(
        client.post(f"/escalations/{escalation_id}/accept", headers=mediator_auth),
        200,
    )
    assert accepted["status"] in {"ACCEPTED", "IN_PROGRESS"}

    outcome = assert_json_response(
        client.post(
            f"/escalations/{escalation_id}/outcome",
            headers=mediator_auth,
            json={
                "outcomeType": "DIALOGUE_HELD",
                "notes": "Dialogue held and follow-up scheduled.",
                "deescalated": True,
                "followUpRequired": True,
            },
        ),
        201,
    )
    assert outcome["outcomeType"] == "DIALOGUE_HELD"

    reporter_status = assert_json_response(client.get(f"/reports/status/{created['trackingCode']}"), 200)
    assert reporter_status["status"] in {"Escalated to trusted mediator", "Closed"}
    assert "Dialogue held" not in str(reporter_status)


def test_related_sahel_reports_create_cluster_before_escalation(client: TestClient) -> None:
    report_texts = [
        "There are rumors that herders will be blocked from the water point tomorrow.",
        "Young men are gathering near the borehole after market day.",
        "A local leader said outsiders should not use the well anymore.",
    ]
    created = [submit_report(client, text) for text in report_texts]
    headers = verifier_headers(client)

    for report in created:
        client.post(f"/reports/{report['reportId']}/process", headers=headers)

    clusters_payload = assert_json_response(client.get("/clusters", headers=headers), 200)
    clusters = clusters_payload.get("items", clusters_payload.get("clusters", []))
    cluster = next(
        (
            candidate
            for candidate in clusters
            if set(report["reportId"] for report in created).issubset(
                set(candidate.get("reportIds", candidate.get("report_ids", [])))
            )
        ),
        None,
    )

    assert cluster is not None
    assert cluster["riskLevel"] in {"HIGH", "CRITICAL"}
    assert cluster["reportCount"] == 3


def test_mediator_action_brief_redacts_reporter_identity_and_precise_location(client: TestClient) -> None:
    created = submit_report(
        client,
        "John from Block C said Amina's shelter behind the exact borehole will be attacked tomorrow.",
    )
    verifier_auth = verifier_headers(client)
    mediator_auth = mediator_headers(client)
    verify_report(client, created["reportId"], verifier_auth)

    escalation = escalate_cluster_or_report(client, created["reportId"], verifier_auth)
    detail = assert_json_response(
        client.get(f"/escalations/{escalation['escalationId']}", headers=mediator_auth),
        200,
    )

    serialized = str(detail)
    assert "John" not in serialized
    assert "Amina" not in serialized
    assert "exact borehole" not in serialized.lower()
    assert "reporter" not in serialized.lower()


def test_dashboard_metrics_are_aggregated_and_privacy_safe(client: TestClient) -> None:
    created = submit_report(client)
    verifier_auth = verifier_headers(client)
    verify_report(client, created["reportId"], verifier_auth)

    payload = assert_json_response(client.get("/dashboard/metrics", headers=verifier_auth), 200)

    assert payload["totalReports"] >= 1
    assert "reportsByCategory" in payload
    assert "riskLevels" in payload
    serialized = str(payload)
    assert created["reportId"] not in serialized
    assert created["trackingCode"] not in serialized
    assert "rawText" not in serialized
    assert "John" not in serialized
