"""Pydantic schemas for fraud detection request and response payloads.

These models enforce strict validation for API inputs and provide a consistent
contract for fraud assessment results returned to clients.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class TelemetryData(BaseModel):
    """Behavioral telemetry captured during a lending application session."""

    typing_speed_wpm: float = Field(..., ge=0.0, description="Typing speed in words per minute.")
    paste_event_count: int = Field(..., ge=0, description="Number of paste events detected.")
    mouse_jitter_score: float = Field(..., ge=0.0, le=1.0, description="Mouse jitter intensity, normalized between 0 and 1.")
    session_duration_seconds: float = Field(..., ge=0.0, description="Session duration in seconds.")
    ip_address: str = Field(..., min_length=1, description="Client IP address.")
    device_fingerprint_id: str = Field(..., min_length=1, description="Unique device fingerprint identifier.")
    is_vpn: bool = Field(..., description="Whether a VPN is detected for the connection.")


class LoanApplicationRequest(BaseModel):
    """Incoming loan application payload for fraud evaluation."""

    applicant_id: str = Field(..., min_length=1, description="Unique applicant identifier.")
    loan_amount: float = Field(..., gt=0.0, description="Requested loan amount in the selected currency.")
    annual_income: float = Field(..., gt=0.0, description="Applicant annual income.")
    requested_term_months: int = Field(..., gt=0, description="Requested repayment term in months.")
    telemetry: TelemetryData = Field(..., description="Behavioral telemetry for the application session.")


class AIExplanation(BaseModel):
    """Structured, auditable explanation of an automated fraud assessment."""

    plain_english_summary: str = Field(
        ..., description="Concise non-technical explanation for compliance officers"
    )
    risk_justification_points: List[str] = Field(
        ..., description="Specific behavioral/financial drivers of the risk score"
    )
    recommended_next_steps: List[str] = Field(
        ..., description="Actionable guidance for fraud analyst review"
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    is_grounded: bool = Field(
        ..., description="Flag indicating whether output passed anti-hallucination verification"
    )


class FraudAssessmentResponse(BaseModel):
    """Fraud assessment result returned to the client after evaluation."""

    application_id: str = Field(..., min_length=1, description="Identifier for the evaluated application.")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Normalized fraud risk score between 0 and 1.")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Aggregated risk category.")
    recommended_action: Literal["APPROVE", "STEP_UP_AUTHENTICATION", "BLOCK"] = Field(..., description="Recommended action based on risk level.")
    top_risk_factors: List[str] = Field(..., description="Top contributing fraud indicators.")
    evaluated_at: str = Field(..., description="ISO 8601 timestamp for assessment completion.")
    explanation: Optional[AIExplanation] = None
    pii_sanitized: bool = False

    @field_validator("evaluated_at")
    @classmethod
    def validate_evaluated_at(cls, value: str) -> str:
        """Ensure the timestamp is a valid ISO 8601 string."""
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("evaluated_at must be a valid ISO 8601 timestamp") from exc
        return value
