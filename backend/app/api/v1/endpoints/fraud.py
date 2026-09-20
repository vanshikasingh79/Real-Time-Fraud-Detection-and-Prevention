"""Fraud evaluation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.models.schemas import FraudAssessmentResponse, LoanApplicationRequest


router = APIRouter()


@router.post("/evaluate", response_model=FraudAssessmentResponse, status_code=status.HTTP_200_OK)
async def evaluate_application(
    request: Request,
    application: LoanApplicationRequest,
    include_explanation: bool = Query(True),
) -> FraudAssessmentResponse:
    """Evaluate a loan application and return its fraud risk assessment."""
    try:
        return await request.app.state.fraud_service.evaluate_application(
            application,
            include_explanation=include_explanation,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fraud evaluation service is unavailable.",
        ) from exc