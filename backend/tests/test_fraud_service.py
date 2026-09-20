"""Tests for fraud assessment API endpoints."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app




@pytest.fixture
def client():
    """Provide a client that runs the application's lifespan hooks."""
    with TestClient(app, headers={"X-API-Key": "fg-sk-dev-hackathon-key-2026"}) as test_client:
        yield test_client


def _application_payload(**overrides: Any) -> dict[str, Any]:
    """Build a valid loan application payload with optional field overrides."""
    payload: dict[str, Any] = {
        "applicant_id": "test-applicant",
        "loan_amount": 25_000,
        "annual_income": 100_000,
        "requested_term_months": 24,
        "telemetry": {
            "typing_speed_wpm": 55,
            "paste_event_count": 0,
            "mouse_jitter_score": 0.4,
            "session_duration_seconds": 180,
            "ip_address": "127.0.0.1",
            "device_fingerprint_id": "test-device",
            "is_vpn": False,
        },
    }
    payload.update(overrides)
    return payload


def test_health_check(client: TestClient) -> None:
    """The health endpoint returns a healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_evaluate_low_risk(client: TestClient) -> None:
    """Normal telemetry produces an approval or step-up decision."""
    response = client.post(
        "/api/v1/fraud/evaluate",
        json=_application_payload(),
    )

    assert response.status_code == 200
    assert response.json()["recommended_action"] in {
        "APPROVE",
        "STEP_UP_AUTHENTICATION",
    }


def test_evaluate_high_risk(client: TestClient) -> None:
    """Extreme telemetry produces a medium or high risk assessment."""
    payload = _application_payload(
        telemetry={
            "typing_speed_wpm": 200,
            "paste_event_count": 10,
            "mouse_jitter_score": 0.9,
            "session_duration_seconds": 10,
            "ip_address": "127.0.0.1",
            "device_fingerprint_id": "suspicious-device",
            "is_vpn": True,
        },
    )
    response = client.post("/api/v1/fraud/evaluate", json=payload)

    assert response.status_code == 200
    assert response.json()["risk_level"] in {"HIGH", "MEDIUM"}


def test_invalid_payload(client: TestClient) -> None:
    """A negative loan amount is rejected by request validation."""
    response = client.post(
        "/api/v1/fraud/evaluate",
        json=_application_payload(loan_amount=-1),
    )

    assert response.status_code == 422
