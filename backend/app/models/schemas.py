"""Pydantic schemas for fraud detection request and response payloads.

These models enforce strict validation for API inputs and provide a consistent
contract for fraud assessment results returned to clients.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, field_validator

class ExplanationResponse(BaseModel):
    summary: str
    risk_factors: list[str]
    is_grounded: bool = True  # Add default fallback value here
class TelemetryData(BaseModel):
    """Behavioral telemetry captured during a lending application session."""

    typing_speed_wpm: float = Field(..., ge=0.0, description="Typing speed in words per minute.")
    paste_event_count: int = Field(..., ge=0, description="Number of paste events detected.")
    mouse_jitter_score: float = Field(..., ge=0.0, le=1.0, description="Mouse jitter intensity, normalized between 0 and 1.")
    session_duration_seconds: float = Field(..., ge=0.0, description="Session duration in seconds.")
    ip_address: str = Field(..., min_length=1, description="Client IP address.")
    device_id: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("device_id", "device_fingerprint_id"),
        description="Explicit device identifier supplied by the client.",
    )
    session_id: str = Field(
        default="",
        min_length=0,
        description="Explicit client session identifier.",
    )
    is_vpn: bool = Field(..., description="Whether a VPN is detected for the connection.")


class LoanApplicationRequest(BaseModel):
    """Incoming loan application payload for fraud evaluation."""

    applicant_id: str = Field(..., min_length=1, description="Unique applicant identifier.")
    user_id: str | None = Field(default=None, min_length=1, description="Explicit user identifier for velocity tracking.")
    loan_amount: float = Field(..., gt=0.0, description="Requested loan amount in the selected currency.")
    annual_income: float = Field(..., gt=0.0, description="Applicant annual income.")
    requested_term_months: int = Field(..., gt=0, description="Requested repayment term in months.")
    telemetry: TelemetryData = Field(..., description="Behavioral telemetry for the application session.")
    is_developer_mode: bool = Field(
        default=False,
        description="Test mode; suppresses historical repeat-offender and vector matching checks.",
    )


class AIExplanation(BaseModel):
    """Structured, auditable explanation of an automated fraud assessment."""

    plain_english_summary: str = Field(
        ..., description="Concise non-technical explanation for compliance officers"
    )
    risk_justification_points: list[str] = Field(
        ..., description="Specific behavioral/financial drivers of the risk score"
    )
    recommended_next_steps: list[str] = Field(
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
    top_risk_factors: list[str] = Field(..., description="Top contributing fraud indicators.")
    evaluated_at: str = Field(..., description="ISO 8601 timestamp for assessment completion.")
    explanation: AIExplanation | None = None
    similar_cases: list[dict] | None = Field(
        default=None,
        description="Historically similar flagged cases used for explainability.",
    )
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


class AsyncEvaluationResponse(BaseModel):
    """Tracking response returned when background evaluation is queued."""

    tracking_id: str
    status: Literal["PENDING", "COMPLETED", "FAILED"]


class EvaluationStatusResponse(BaseModel):
    """Current background evaluation state and optional decision payload."""

    tracking_id: str
    status: Literal["PENDING", "COMPLETED", "FAILED"]
    evaluation_id: str
    risk_score: float | None = None
    risk_level: str | None = None
    decision: FraudAssessmentResponse | None = None


class AnalystOverrideRequest(BaseModel):
    """Analyst decision override payload."""

    evaluation_id: str
    analyst_id: str = Field(..., min_length=1)
    new_decision: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
