"""Application service for evaluating loan application fraud risk."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib

from app.core.config import settings
from app.ml.model import FraudScorer
from app.models.schemas import FraudAssessmentResponse, LoanApplicationRequest


class FraudEvaluationService:
    """Load the fraud model and evaluate loan applications."""

    def __init__(self) -> None:
        """Load the configured fraud model for subsequent evaluations.

        Raises:
            RuntimeError: If the model file is missing, unreadable, or invalid.
        """
        model_path = self._resolve_model_path(settings.MODEL_PATH)
        try:
            loaded_model: Any = joblib.load(model_path)
        except Exception as exc:
            raise RuntimeError(
                f"Unable to load fraud model from '{model_path}'."
            ) from exc

        if isinstance(loaded_model, FraudScorer):
            self.scorer = loaded_model
        else:
            self.scorer = FraudScorer(model=loaded_model)

    @staticmethod
    def _resolve_model_path(model_path: str) -> Path:
        """Resolve a configured model path independently of the launch directory."""
        path = Path(model_path)
        if path.is_absolute():
            return path
        backend_root = Path(__file__).resolve().parents[2]
        return backend_root / path

    def evaluate_application(
        self,
        application: LoanApplicationRequest,
    ) -> FraudAssessmentResponse:
        """Evaluate an application and return its validated fraud assessment.

        Args:
            application: Validated loan application request to assess.

        Returns:
            A validated assessment containing the score, risk category, action,
            and observable risk factors.

        Raises:
            RuntimeError: If the loaded model cannot score the application.
        """
        try:
            risk_score, risk_factors = self.scorer.predict_risk(
                telemetry=application.telemetry,
                loan_amount=application.loan_amount,
                annual_income=application.annual_income,
            )
        except Exception as exc:
            raise RuntimeError("Unable to evaluate the loan application.") from exc

        if risk_score >= settings.FRAUD_THRESHOLD_HIGH:
            risk_level = "HIGH"
            recommended_action = "BLOCK"
        elif risk_score >= settings.FRAUD_THRESHOLD_MEDIUM:
            risk_level = "MEDIUM"
            recommended_action = "STEP_UP_AUTHENTICATION"
        else:
            risk_level = "LOW"
            recommended_action = "APPROVE"

        return FraudAssessmentResponse(
            application_id=application.applicant_id,
            risk_score=risk_score,
            risk_level=risk_level,
            recommended_action=recommended_action,
            top_risk_factors=risk_factors,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )
