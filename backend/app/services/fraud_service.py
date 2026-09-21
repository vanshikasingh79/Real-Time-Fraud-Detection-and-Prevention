"""Application service for evaluating loan application fraud risk."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import joblib
from sqlalchemy import func, select

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import FraudAuditLog
from app.ml.model import FraudScorer
from app.models.schemas import FraudAssessmentResponse, LoanApplicationRequest
from app.services.explainability_service import ExplainabilityEngine
from app.services.vector_service import VectorSimilarityEngine

logger = logging.getLogger(__name__)


class FraudEvaluationService:
    """Load the fraud model and evaluate loan applications."""

    def __init__(
        self,
        explainability_engine: ExplainabilityEngine | None = None,
        vector_engine: VectorSimilarityEngine | None = None,
    ) -> None:
        """Load the configured fraud model for subsequent evaluations.

        Raises:
            RuntimeError: If the model file is missing, unreadable, or invalid.
        """
        self.explainability_engine = explainability_engine or ExplainabilityEngine()
        self.vector_engine = vector_engine or VectorSimilarityEngine()
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

    async def evaluate_application(
        self,
        application: LoanApplicationRequest,
        include_explanation: bool = True,
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
            feature_vector = FraudScorer.extract_features(
                application.telemetry,
                application.loan_amount,
                application.annual_income,
            ).flatten().tolist()
            repeat_offender = False
            similar_cases: list[dict] = []
            if not application.is_developer_mode:
                with SessionLocal() as database:
                    repeat_offender = self._is_repeat_offender(
                        database,
                        application.telemetry.device_fingerprint_id,
                    )
                    similar_cases = self.vector_engine.find_similar_cases(
                        database,
                        feature_vector,
                    )
            risk_score, risk_factors = self.scorer.predict_risk(
                telemetry=application.telemetry,
                loan_amount=application.loan_amount,
                annual_income=application.annual_income,
            )
        except Exception as exc:
            raise RuntimeError("Unable to evaluate the loan application.") from exc

        if repeat_offender:
            risk_score = max(risk_score, settings.REPEAT_OFFENDER_RISK_WEIGHT)
            risk_factors.append(
                "Repeat offender: Device fingerprint previously flagged for high fraud risk"
            )
        if application.is_developer_mode:
            risk_factors.append(
                "Developer Test Mode Active: Suppressed repeat-offender DB lookup "
                "and historical vector pattern matching."
            )

        if risk_score >= settings.FRAUD_THRESHOLD_HIGH:
            risk_level = "HIGH"
            recommended_action = "BLOCK"
        elif risk_score >= settings.FRAUD_THRESHOLD_MEDIUM:
            risk_level = "MEDIUM"
            recommended_action = "STEP_UP_AUTHENTICATION"
        else:
            risk_level = "LOW"
            recommended_action = "APPROVE"

        explanation = None
        pii_sanitized = False
        if include_explanation:
            explanation = await self.explainability_engine.generate_explanation(
                application=application,
                risk_score=risk_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                similar_cases=similar_cases,
            )
            pii_sanitized = True

        response = FraudAssessmentResponse(
            application_id=application.applicant_id,
            risk_score=risk_score,
            risk_level=risk_level,
            recommended_action=recommended_action,
            top_risk_factors=risk_factors,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            explanation=explanation,
            pii_sanitized=pii_sanitized,
        )
        self._save_audit_log(application, response, feature_vector)
        return response

    @staticmethod
    def _is_repeat_offender(database: Any, device_fingerprint_id: str) -> bool:
        """Return whether a device has at least two recent high-risk decisions."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        try:
            high_risk_count = database.scalar(
                select(func.count(FraudAuditLog.id)).where(
                    FraudAuditLog.device_fingerprint_id == device_fingerprint_id,
                    FraudAuditLog.risk_level == "HIGH",
                    FraudAuditLog.timestamp >= cutoff,
                )
            )
            return bool(high_risk_count and high_risk_count >= 2)
        except Exception:
            logger.exception(
                "fraud_audit_lookup_failed",
                extra={"device_fingerprint_id": device_fingerprint_id},
            )
            return False

    @staticmethod
    def _save_audit_log(
        application: LoanApplicationRequest,
        response: FraudAssessmentResponse,
        feature_vector: list[float],
    ) -> None:
        """Persist a completed decision and log the database save outcome."""
        try:
            with SessionLocal() as database:
                database.add(
                    FraudAuditLog(
                        application_id=response.application_id,
                        applicant_id=application.applicant_id,
                        device_fingerprint_id=application.telemetry.device_fingerprint_id,
                        ip_address=application.telemetry.ip_address,
                        risk_score=response.risk_score,
                        risk_level=response.risk_level,
                        recommended_action=response.recommended_action,
                        risk_factors=json.dumps(response.top_risk_factors),
                        feature_vector=json.dumps(feature_vector),
                    )
                )
                database.commit()
            logger.info(
                "fraud_evaluation_completed",
                extra={
                    "application_id": response.application_id,
                    "score": response.risk_score,
                    "action": response.recommended_action,
                    "database_save_status": "success",
                },
            )
        except Exception:
            logger.exception(
                "fraud_evaluation_completed",
                extra={
                    "application_id": response.application_id,
                    "score": response.risk_score,
                    "action": response.recommended_action,
                    "database_save_status": "failed",
                },
            )
