"""HTTP endpoints for fraud evaluation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import FraudAssessmentResponse, LoanApplicationRequest
from app.services.fraud_service import FraudEvaluationService


router = APIRouter()


@router.post(
    "/evaluate",
    response_model=FraudAssessmentResponse,
    status_code=status.HTTP_200_OK,
)
def evaluate_application(
    application: LoanApplicationRequest,
) -> FraudAssessmentResponse:
    """Evaluate a loan application and return its fraud risk assessment.

    Raises:
        HTTPException: If the model cannot be loaded or the application cannot
            be evaluated.
    """
    try:
        service = FraudEvaluationService()
        return service.evaluate_application(application)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fraud evaluation service is unavailable.",
        ) from exc