"""Backward-compatible imports for the split ML modules."""

from app.ml.model import FraudScorer
from app.ml.trainer import generate_synthetic_data, train_and_save

__all__ = ["FraudScorer", "generate_synthetic_data", "train_and_save"]


if __name__ == "__main__":
    train_and_save("app/ml/artifacts/saved_model.pkl")