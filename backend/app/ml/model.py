"""Fraud scoring model wrapper."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest

from app.core.config import settings
from app.models.schemas import TelemetryData


class FraudScorer:
    """Wrapper around IsolationForest for real-time risk scoring."""

    def __init__(self, model: IsolationForest) -> None:
        """Initialize the scorer with a trained IsolationForest model."""
        self.model = model

    @staticmethod
    def extract_features(
        telemetry: TelemetryData, loan_amount: float, annual_income: float
    ) -> np.ndarray:
        """Extract a 2D feature vector from telemetry and financial inputs."""
        loan_to_income_ratio = loan_amount / annual_income if annual_income > 0 else 0.0
        return np.array(
            [[
                float(telemetry.typing_speed_wpm),
                float(telemetry.paste_event_count),
                float(telemetry.mouse_jitter_score),
                float(telemetry.session_duration_seconds),
                1.0 if telemetry.is_vpn else 0.0,
                float(loan_to_income_ratio),
            ]]
        )

    def predict_risk(
        self, telemetry: TelemetryData, loan_amount: float, annual_income: float
    ) -> Tuple[float, List[str]]:
        """Predict normalized risk and identify model-supported risk factors."""
        features = self.extract_features(telemetry, loan_amount, annual_income)
        raw_score = self.model.decision_function(features)[0]
        normalized_risk = float(np.clip(0.5 - raw_score, 0.0, 1.0))

        risk_factors: List[str] = []
        if telemetry.paste_event_count > settings.PASTE_COUNT_THRESHOLD:
            risk_factors.append("High paste event count detected (possible autofill/stolen PII)")
        if telemetry.is_vpn:
            risk_factors.append("Anonymized network connection detected (VPN/Proxy)")
        if (
            telemetry.typing_speed_wpm > settings.TYPING_WPM_HIGH
            or telemetry.typing_speed_wpm < settings.TYPING_WPM_LOW
        ):
            risk_factors.append("Anomalous typing cadence detected")
        if telemetry.mouse_jitter_score < settings.MOUSE_JITTER_LOW:
            risk_factors.append("Lack of human mouse movement (possible script execution)")
        if (
            loan_amount / annual_income if annual_income > 0 else 0
        ) > settings.LOAN_TO_INCOME_RATIO_HIGH:
            risk_factors.append("High loan-to-income ratio request")
        if not risk_factors:
            risk_factors.append("Standard telemetry within normal variance")

        return round(normalized_risk, 4), risk_factors