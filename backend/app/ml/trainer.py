"""Synthetic data generation and fraud model training."""

from __future__ import annotations

import os
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from app.ml.model import FraudScorer


def generate_synthetic_data(num_samples: int = 1000) -> np.ndarray:
    """Generate synthetic normal applicant telemetry for model training."""
    np.random.seed(42)
    return np.column_stack(
        [
            np.random.normal(50, 15, num_samples),
            np.random.poisson(0.5, num_samples),
            np.random.uniform(0.2, 0.8, num_samples),
            np.random.normal(120, 30, num_samples),
            np.random.binomial(1, 0.05, num_samples),
            np.random.uniform(0.05, 0.35, num_samples),
        ]
    )


def train_and_save(model_path: str) -> None:
    """Train an IsolationForest model and save a FraudScorer artifact."""
    print("Generating synthetic telemetry dataset...")
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(generate_synthetic_data())

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(FraudScorer(model), model_path)
    print(f"Model successfully trained and saved to: {model_path}")


if __name__ == "__main__":
    train_and_save(os.path.join(os.path.dirname(__file__), "artifacts", "saved_model.pkl"))