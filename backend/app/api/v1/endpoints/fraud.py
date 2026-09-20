"""Fraud evaluation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import FraudAssessmentResponse, LoanApplicationRequest


router = APIRouter()


@router.post("/evaluate", response_model=FraudAssessmentResponse, status_code=status.HTTP_200_OK)
def evaluate_application(
    request: Request,
    application: LoanApplicationRequest,
) -> FraudAssessmentResponse:
    """Evaluate a loan application and return its fraud risk assessment."""
    try:
        return request.app.state.fraud_service.evaluate_application(application)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fraud evaluation service is unavailable.",
        ) from exc