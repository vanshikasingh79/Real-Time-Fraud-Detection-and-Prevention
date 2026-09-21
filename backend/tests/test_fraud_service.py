"""Tests for fraud assessment API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient





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
    """The versioned health endpoint returns runtime diagnostics."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_evaluate_low_risk(client: TestClient) -> None:
    """Normal telemetry produces an approval or step-up decision."""
    response = client.post(
        "/api/v1/fraud/evaluate",
        json=_application_payload(
            telemetry={
                "typing_speed_wpm": 55,
                "paste_event_count": 0,
                "mouse_jitter_score": 0.4,
                "session_duration_seconds": 180,
                "ip_address": "127.0.0.1",
                "device_fingerprint_id": "low-risk-regression-device",
                "is_vpn": False,
            },
        ),
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


def test_extreme_financial_anomaly_is_high_without_repeat_history(client: TestClient) -> None:
    """An unrealistic loan-to-income ratio independently produces HIGH risk."""
    response = client.post(
        "/api/v1/fraud/evaluate?include_explanation=true",
        json=_application_payload(
            applicant_id="new-financial-anomaly",
            loan_amount=25_000,
            annual_income=100,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "HIGH"
    assert body["risk_score"] >= 0.80
    assert any("EXTREME_FINANCIAL_ANOMALY" in factor for factor in body["top_risk_factors"])
    assert any(
        "Requested loan amount ($25,000) severely exceeds reported income ($100)." in point
        for point in body["explanation"]["risk_justification_points"]
    )


def test_legitimate_financial_ratio_remains_low(client: TestClient) -> None:
    """A normal loan-to-income ratio does not receive the extreme rule weight."""
    response = client.post(
        "/api/v1/fraud/evaluate?include_explanation=false",
        json=_application_payload(
            applicant_id="normal-financial-profile",
            loan_amount=5_000,
            annual_income=6_000,
            telemetry={
                "typing_speed_wpm": 55,
                "paste_event_count": 0,
                "mouse_jitter_score": 0.4,
                "session_duration_seconds": 180,
                "ip_address": "127.0.0.1",
                "device_fingerprint_id": "normal-financial-profile-device",
                "is_vpn": False,
            },
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] < 0.50
    assert not any("EXTREME_FINANCIAL_ANOMALY" in factor for factor in body["top_risk_factors"])


def test_developer_mode_suppresses_historical_signals(client: TestClient) -> None:
    """Developer mode keeps live rules while suppressing historical evidence."""
    response = client.post(
        "/api/v1/fraud/evaluate?include_explanation=true",
        json=_application_payload(
            applicant_id="developer-mode-check",
            is_developer_mode=True,
            loan_amount=25_000,
            annual_income=100,
            telemetry={
                "typing_speed_wpm": 200,
                "paste_event_count": 8,
                "mouse_jitter_score": 0.0,
                "session_duration_seconds": 10,
                "ip_address": "127.0.0.1",
                "device_fingerprint_id": "DEV-DEMO-10294",
                "is_vpn": True,
            },
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "HIGH"
    assert any("EXTREME_FINANCIAL_ANOMALY" in factor for factor in body["top_risk_factors"])
    assert any("Developer Test Mode Active" in factor for factor in body["top_risk_factors"])
    assert not any("Pattern Match:" in point for point in body["explanation"]["risk_justification_points"])
