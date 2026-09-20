"""Offline benchmark for the Fraud Guard Isolation Forest model."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings
from app.models.schemas import TelemetryData


SAMPLE_COUNT = 1_000
LEGITIMATE_COUNT = 850
FRAUD_COUNT = 150


def generate_labeled_test_set() -> list[tuple[TelemetryData, float, float, int]]:
    """Generate 850 legitimate and 150 labeled fraudulent applications."""
    rng = np.random.default_rng(2026)
    samples: list[tuple[TelemetryData, float, float, int]] = []

    for index in range(LEGITIMATE_COUNT):
        annual_income = float(rng.uniform(50_000, 160_000))
        loan_amount = float(annual_income * rng.uniform(0.10, 0.45))
        samples.append(
            (
                TelemetryData(
                    typing_speed_wpm=float(rng.uniform(40, 90)),
                    paste_event_count=0,
                    mouse_jitter_score=float(rng.uniform(0.5, 0.9)),
                    session_duration_seconds=float(rng.uniform(30, 180)),
                    ip_address=f"192.168.{index % 200}.{index % 240 + 1}",
                    device_fingerprint_id=f"LEGIT-{index:04d}",
                    is_vpn=False,
                ),
                loan_amount,
                annual_income,
                0,
            )
        )

    for index in range(FRAUD_COUNT):
        vector = index % 3
        if vector == 0:
            typing_speed = float(rng.uniform(181, 240))
            paste_count = int(rng.integers(5, 11))
            jitter = float(rng.uniform(0.0, 0.049))
            session_duration = float(rng.uniform(10, 90))
            loan_to_income_ratio = float(rng.uniform(0.2, 0.6))
            is_vpn = False
        elif vector == 1:
            typing_speed = float(rng.uniform(40, 100))
            paste_count = int(rng.integers(5, 11))
            jitter = float(rng.uniform(0.2, 0.8))
            session_duration = float(rng.uniform(20, 180))
            loan_to_income_ratio = float(rng.uniform(0.81, 1.4))
            is_vpn = True
        else:
            typing_speed = float(rng.uniform(221, 280))
            paste_count = 0
            jitter = 0.0
            session_duration = float(rng.uniform(1, 4.9))
            loan_to_income_ratio = float(rng.uniform(0.2, 0.6))
            is_vpn = False

        annual_income = float(rng.uniform(50_000, 160_000))
        samples.append(
            (
                TelemetryData(
                    typing_speed_wpm=typing_speed,
                    paste_event_count=paste_count,
                    mouse_jitter_score=jitter,
                    session_duration_seconds=session_duration,
                    ip_address=f"10.0.{vector}.{index + 1}",
                    device_fingerprint_id=f"FRAUD-{index:04d}",
                    is_vpn=is_vpn,
                ),
                annual_income * loan_to_income_ratio,
                annual_income,
                1,
            )
        )

    return samples


def calculate_metrics(labels: list[int], predictions: list[int]) -> dict[str, Any]:
    """Calculate confusion-matrix counts and classification metrics."""
    true_positive = sum(label == 1 and prediction == 1 for label, prediction in zip(labels, predictions))
    false_positive = sum(label == 0 and prediction == 1 for label, prediction in zip(labels, predictions))
    true_negative = sum(label == 0 and prediction == 0 for label, prediction in zip(labels, predictions))
    false_negative = sum(label == 1 and prediction == 0 for label, prediction in zip(labels, predictions))

    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    false_positive_rate = false_positive / (false_positive + true_negative) if false_positive + true_negative else 0.0

    return {
        "sample_count": len(labels),
        "confusion_matrix": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "false_positive_rate": false_positive_rate,
        },
        "threshold": settings.FRAUD_THRESHOLD_MEDIUM,
    }


def print_report(report: dict[str, Any]) -> None:
    """Print a compact ASCII benchmark report."""
    matrix = report["confusion_matrix"]
    metrics = report["metrics"]
    print("Fraud Guard Isolation Forest Benchmark")
    print("=" * 42)
    print("Confusion Matrix")
    print("+----------------------+----------+")
    print("| Outcome              | Count    |")
    print("+----------------------+----------+")
    for label, key in (
        ("True Positive (TP)", "true_positive"),
        ("False Positive (FP)", "false_positive"),
        ("True Negative (TN)", "true_negative"),
        ("False Negative (FN)", "false_negative"),
    ):
        print(f"| {label:<20} | {matrix[key]:>8} |")
    print("+----------------------+----------+")
    print("Metrics")
    print("+----------------------+----------+")
    for label, key in (
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("F1-Score", "f1_score"),
        ("False Positive Rate", "false_positive_rate"),
    ):
        print(f"| {label:<20} | {metrics[key]:>7.2%} |")
    print("+----------------------+----------+")


def main() -> int:
    """Run the offline benchmark and save its JSON report."""
    model_path = BACKEND_ROOT / "app" / "ml" / "artifacts" / "saved_model.pkl"
    scorer = joblib.load(model_path)
    samples = generate_labeled_test_set()

    labels: list[int] = []
    predictions: list[int] = []
    for telemetry, loan_amount, annual_income, label in samples:
        risk_score, _ = scorer.predict_risk(telemetry, loan_amount, annual_income)
        labels.append(label)
        predictions.append(int(risk_score >= settings.FRAUD_THRESHOLD_MEDIUM))

    report = calculate_metrics(labels, predictions)
    report["model_path"] = str(model_path)
    print_report(report)

    report_path = PROJECT_ROOT / "reports" / "model_evaluation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report saved to {report_path}")

    metrics = report["metrics"]
    assert metrics["false_positive_rate"] <= 0.05, "False Positive Rate exceeded 5%"
    assert metrics["recall"] >= 0.85, "Recall fell below 85%"
    print("[PASS] FPR <= 5% and Recall >= 85%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
