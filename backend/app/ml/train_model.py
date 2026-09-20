"""Machine learning model pipeline for real-time anomaly detection.

Trains an IsolationForest model on behavioral biometrics and financial signals
to score digital lending application fraud risk.
"""

import os
import sys
from typing import Any, Dict, List, Tuple
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from app.models.schemas import TelemetryData


class FraudScorer:
    """Wrapper class around IsolationForest for real-time risk scoring."""

    def __init__(self, model: IsolationForest) -> None:
        """Initialize the scorer with a trained IsolationForest model."""
        self.model = model

    @staticmethod
    def extract_features(
        telemetry: TelemetryData, loan_amount: float, annual_income: float
    ) -> np.ndarray:
        """Extract a 2D feature vector from telemetry and financial inputs."""
        loan_to_income_ratio = (
            loan_amount / annual_income if annual_income > 0 else 0.0
        )
        return np.array(
            [
                [
                    float(telemetry.typing_speed_wpm),
                    float(telemetry.paste_event_count),
                    float(telemetry.mouse_jitter_score),
                    float(telemetry.session_duration_seconds),
                    1.0 if telemetry.is_vpn else 0.0,
                    float(loan_to_income_ratio),
                ]
            ]
        )

    def predict_risk(
        self, telemetry: TelemetryData, loan_amount: float, annual_income: float
    ) -> Tuple[float, List[str]]:
        """Predict normalized risk score (0.0 to 1.0) and extract top risk factors."""
        features = self.extract_features(telemetry, loan_amount, annual_income)

        # IsolationForest decision_function outputs negative values for anomalies,
        # and positive values for normal instances.
        raw_score = self.model.decision_function(features)[0]

        # Normalize raw score (-0.5 to 0.5 typical range) to a 0.0 - 1.0 risk score
        normalized_risk = float(np.clip(0.5 - raw_score, 0.0, 1.0))

        # Identify specific risk indicators
        risk_factors: List[str] = []
        if telemetry.paste_event_count > 3:
            risk_factors.append("High paste event count detected (possible autofill/stolen PII)")
        if telemetry.is_vpn:
            risk_factors.append("Anonymized network connection detected (VPN/Proxy)")
        if telemetry.typing_speed_wpm > 150.0 or telemetry.typing_speed_wpm < 10.0:
            risk_factors.append("Anomalous typing cadence detected")
        if telemetry.mouse_jitter_score < 0.05:
            risk_factors.append("Lack of human mouse movement (possible script execution)")
        if (loan_amount / annual_income if annual_income > 0 else 0) > 0.5:
            risk_factors.append("High loan-to-income ratio request")

        if not risk_factors:
            risk_factors.append("Standard telemetry within normal variance")

        return round(normalized_risk, 4), risk_factors


def generate_synthetic_data(num_samples: int = 1000) -> np.ndarray:
    """Generate synthetic 'normal' applicant telemetry for model training."""
    np.random.seed(42)

    typing_speed = np.random.normal(50, 15, num_samples)  # Normal typing: ~50 WPM
    paste_count = np.random.poisson(0.5, num_samples)      # Low paste count
    mouse_jitter = np.random.uniform(0.2, 0.8, num_samples) # Normal human jitter
    session_dur = np.random.normal(120, 30, num_samples)   # Session length ~2 mins
    is_vpn = np.random.binomial(1, 0.05, num_samples)      # 5% VPN rate
    loan_to_income = np.random.uniform(0.05, 0.35, num_samples) # Reasonable ratio

    return np.column_stack(
        [
            typing_speed,
            paste_count,
            mouse_jitter,
            session_dur,
            is_vpn,
            loan_to_income,
        ]
    )


def train_and_save(model_path: str) -> None:
    """Train the IsolationForest anomaly model and save to disk via joblib."""
    print("Generating synthetic telemetry dataset...")
    X_train = generate_synthetic_data()

    print("Training IsolationForest anomaly detection model...")
    model = IsolationForest(
        n_estimators=100, contamination=0.05, random_state=42
    )
    model.fit(X_train)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    if __name__ == "__main__":
        sys.modules["app.ml.train_model"] = sys.modules[__name__]
    FraudScorer.__module__ = "app.ml.train_model"
    scorer = FraudScorer(model)
    joblib.dump(scorer, model_path)
    print(f"✅ Model successfully trained and saved to: {model_path}")


if __name__ == "__main__":
    # Resolve absolute path to app/ml/saved_model.pkl
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(current_dir, "saved_model.pkl")

    train_and_save(target_path)