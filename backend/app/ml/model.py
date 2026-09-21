"""Fraud scoring model wrapper."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.models.schemas import TelemetryData


class FraudScorer:
    """Wrapper around IsolationForest for real-time risk scoring."""

    def __init__(
        self,
        model: IsolationForest,
        scaler: StandardScaler,
        score_min: float = -0.5,
        score_max: float = 0.5,
    ) -> None:
        """Initialize the scorer with a model and its training score bounds."""
        self.model = model
        self.scaler = scaler
        self.score_min = score_min
        self.score_max = score_max

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
        scaled_features = self.scaler.transform(features)
        raw_score = float(self.model.decision_function(scaled_features)[0])
        score_span = self.score_max - self.score_min or 1e-9
        model_risk = float(
            np.clip((self.score_max - raw_score) / score_span, 0.0, 1.0)
        )
        lti_ratio = loan_amount / max(annual_income, 1.0)
        lti_scale = max(settings.LTI_RISK_SCALE, 1e-9)
        scaled_lti = lti_ratio / lti_scale
        lti_risk = float(scaled_lti / (1.0 + scaled_lti))
        telemetry_signals = [
            telemetry.paste_event_count >= settings.PASTE_COUNT_THRESHOLD,
            telemetry.is_vpn,
            telemetry.typing_speed_wpm >= settings.TYPING_WPM_HIGH
            or telemetry.typing_speed_wpm <= settings.TYPING_WPM_LOW,
            telemetry.mouse_jitter_score <= settings.MOUSE_JITTER_LOW,
        ]
        telemetry_risk = sum(telemetry_signals) / len(telemetry_signals)
        weight_total = (
            settings.MODEL_RISK_WEIGHT
            + settings.LTI_RISK_WEIGHT
            + settings.TELEMETRY_RISK_WEIGHT
        ) or 1.0
        normalized_risk = float(
            np.clip(
                (
                    settings.MODEL_RISK_WEIGHT * model_risk
                    + settings.LTI_RISK_WEIGHT * lti_risk
                    + settings.TELEMETRY_RISK_WEIGHT * telemetry_risk
                )
                / weight_total,
                0.0,
                1.0,
            )
        )
        risk_factors: List[str] = []
        if telemetry.paste_event_count >= settings.PASTE_COUNT_THRESHOLD:
            risk_factors.append("High paste event count detected (possible autofill/stolen PII)")
        if telemetry.is_vpn:
            risk_factors.append("Anonymized network connection detected (VPN/Proxy)")
        if (
            telemetry.typing_speed_wpm >= settings.TYPING_WPM_HIGH
            or telemetry.typing_speed_wpm <= settings.TYPING_WPM_LOW
        ):
            risk_factors.append("Anomalous typing cadence detected")
        if telemetry.mouse_jitter_score <= settings.MOUSE_JITTER_LOW:
            risk_factors.append("Lack of human mouse movement (possible script execution)")
        risk_factors.append(f"Loan-to-income ratio is {lti_ratio:.2f}")
        if not risk_factors:
            risk_factors.append("Standard telemetry within normal variance")

        return float(normalized_risk), risk_factors