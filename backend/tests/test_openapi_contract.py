from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

OPENAPI_PATH = Path(__file__).resolve().parents[1] / "app" / "openapi.yaml"
REQUIRED_OPERATIONS = {
    ("post", "/reports"),
    ("get", "/reports/status/{trackingCode}"),
    ("get", "/reports"),
    ("get", "/reports/{reportId}"),
    ("post", "/reports/{reportId}/process"),
    ("post", "/reports/{reportId}/verify"),
    ("get", "/clusters"),
    ("get", "/clusters/{clusterId}"),
    ("post", "/clusters/{clusterId}/verify"),
    ("post", "/clusters/{clusterId}/escalate"),
    ("get", "/escalations"),
    ("get", "/escalations/{escalationId}"),
    ("post", "/escalations/{escalationId}/accept"),
    ("post", "/escalations/{escalationId}/outcome"),
    ("post", "/auth/login"),
    ("get", "/dashboard/metrics"),
    ("get", "/status"),
}
FORBIDDEN_WORKFLOW_TERMS = ("moder" + "ator", "respon" + "der", "Umoja" + "Signal")


@pytest.fixture()
def openapi_contract() -> dict[str, Any]:
    with OPENAPI_PATH.open("r", encoding="utf-8") as contract_file:
        contract = yaml.safe_load(contract_file)
    assert isinstance(contract, dict)
    return contract


def test_openapi_yaml_is_valid_and_named_for_sautirelay(openapi_contract: dict[str, Any]) -> None:
    assert openapi_contract["openapi"].startswith("3.")
    assert openapi_contract["info"]["title"] == "SautiRelay API"


def test_openapi_defines_planned_backend_routes(openapi_contract: dict[str, Any]) -> None:
    paths = openapi_contract.get("paths", {})
    missing = [
        f"{method.upper()} {path}" for method, path in sorted(REQUIRED_OPERATIONS) if method not in paths.get(path, {})
    ]
    assert not missing, f"OpenAPI contract is missing planned operations: {missing}"


def test_openapi_uses_mediator_naming_only() -> None:
    text = OPENAPI_PATH.read_text(encoding="utf-8")
    assert re.search(r"\bmediator\b", text, flags=re.IGNORECASE)
    for forbidden in FORBIDDEN_WORKFLOW_TERMS:
        assert not re.search(rf"\b{forbidden}\b", text, flags=re.IGNORECASE), (
            f"Use mediator/SautiRelay naming only; found {forbidden!r} in OpenAPI."
        )


def test_implemented_routes_are_represented_in_openapi(client: Any, openapi_contract: dict[str, Any]) -> None:
    documented = {
        (method.upper(), path)
        for path, methods in openapi_contract.get("paths", {}).items()
        for method in methods
        if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}
    }
    implemented = {
        (method, route.path)
        for route in client.app.routes
        if getattr(route, "include_in_schema", True)
        for method in getattr(route, "methods", set())
        if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}
    }
    missing = sorted(implemented - documented)
    assert not missing, f"Implemented routes missing from backend/app/openapi.yaml: {missing}"
