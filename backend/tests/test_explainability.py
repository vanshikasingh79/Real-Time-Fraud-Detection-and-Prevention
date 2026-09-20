"""Tests for Responsible AI guardrails and explanation responses."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.guardrails import AIGuardrailService
from app.main import app
from app.models.schemas import LoanApplicationRequest, TelemetryData


@pytest.fixture
def client():
    """Provide a TestClient with FastAPI lifespan enabled."""
    with TestClient(app) as test_client:
        yield test_client


def _application() -> LoanApplicationRequest:
    """Build a representative application containing identifiable telemetry."""
    return LoanApplicationRequest(
        applicant_id="applicant-secret",
        loan_amount=25_000,
        annual_income=100_000,
        requested_term_months=24,
        telemetry=TelemetryData(
            typing_speed_wpm=55,
            paste_event_count=4,
            mouse_jitter_score=0.4,
            session_duration_seconds=180,
            ip_address="192.168.1.1",
            device_fingerprint_id="DEV-99211",
            is_vpn=True,
        ),
    )


def _application_payload() -> dict[str, Any]:
    """Build a valid request payload for the evaluation endpoint."""
    return _application().model_dump()


def test_pii_sanitization() -> None:
    """PII is masked while assessment fields remain available."""
    sanitized = AIGuardrailService().sanitize_payload(_application())

    assert sanitized["applicant_id"] == "ANONYMIZED_APPLICANT"
    assert sanitized["telemetry"]["ip_address"] == "192.168.x.x"
    assert sanitized["telemetry"]["device_fingerprint_id"] == "DEV-***-211"
    assert sanitized["loan_amount"] == 25_000
    assert sanitized["annual_income"] == 100_000
    assert sanitized["telemetry"]["typing_speed_wpm"] == 55
    assert sanitized["telemetry"]["paste_event_count"] == 4
    assert sanitized["telemetry"]["mouse_jitter_score"] == 0.4


def test_grounding_verification_pass() -> None:
    """Matching explanation points are accepted as grounded."""
    guardrails = AIGuardrailService()

    assert guardrails.verify_grounding(
        ["VPN activity detected", "High paste count"],
        [
            "Anonymized network connection detected (VPN/Proxy)",
            "High paste event count detected",
        ],
    ) is True


def test_grounding_verification_fail() -> None:
    """Unsupported hallucinated factors are rejected."""
    guardrails = AIGuardrailService()

    assert guardrails.verify_grounding(
        ["Credit score failure detected"],
        ["Anonymized network connection detected (VPN/Proxy)"],
    ) is False


def test_evaluate_endpoint_with_explanation(client: TestClient) -> None:
    """The evaluation endpoint returns a grounded explanation by default."""
    response = client.post(
        "/api/v1/fraud/evaluate?include_explanation=true",
        json=_application_payload(),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["explanation"] is not None
    assert body["pii_sanitized"] is True
