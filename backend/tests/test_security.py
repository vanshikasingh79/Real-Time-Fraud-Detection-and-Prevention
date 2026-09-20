"""Tests for protected fraud evaluation endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


PAYLOAD = {
    "applicant_id": "security-test",
    "loan_amount": 25_000,
    "annual_income": 100_000,
    "requested_term_months": 24,
    "telemetry": {
        "typing_speed_wpm": 55,
        "paste_event_count": 0,
        "mouse_jitter_score": 0.4,
        "session_duration_seconds": 180,
        "ip_address": "127.0.0.1",
        "device_fingerprint_id": "security-device",
        "is_vpn": False,
    },
}


def test_evaluate_without_api_key_returns_401() -> None:
    """Requests without an API key are rejected."""
    with TestClient(app) as client:
        response = client.post("/api/v1/fraud/evaluate", json=PAYLOAD)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API Key"


def test_evaluate_with_incorrect_api_key_returns_401() -> None:
    """Requests with an invalid API key are rejected."""
    with TestClient(app, headers={"X-API-Key": "wrong-key"}) as client:
        response = client.post("/api/v1/fraud/evaluate", json=PAYLOAD)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API Key"


def test_evaluate_with_valid_api_key_succeeds() -> None:
    """Requests with the configured development key are accepted."""
    with TestClient(
        app,
        headers={"X-API-Key": "fg-sk-dev-hackathon-key-2026"},
    ) as client:
        response = client.post("/api/v1/fraud/evaluate", json=PAYLOAD)

    assert response.status_code == 200