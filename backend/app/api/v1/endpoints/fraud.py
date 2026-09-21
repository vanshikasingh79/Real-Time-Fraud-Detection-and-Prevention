"""Fraud evaluation API endpoints."""

from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.database import get_db
from app.db.models import EvaluationLog
from app.core.rate_limit import limiter
from app.models.schemas import (
    AsyncEvaluationResponse,
    EvaluationStatusResponse,
    FraudAssessmentResponse,
    LoanApplicationRequest,
)


router = APIRouter()


@router.post(
    "/evaluate",
    response_model=FraudAssessmentResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("20/minute")
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


@router.post(
    "/evaluate-async",
    response_model=AsyncEvaluationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit("20/minute")
async def evaluate_application_async(
    request: Request,
    background_tasks: BackgroundTasks,
    application: LoanApplicationRequest,
    database: Session = Depends(get_db),
) -> AsyncEvaluationResponse:
    """Queue an evaluation and return a tracking ID immediately."""
    tracking_id = str(uuid4())
    evaluation = EvaluationLog(
        id=str(uuid4()),
        tracking_id=tracking_id,
        user_id=application.user_id or application.applicant_id,
        device_id=application.telemetry.device_id,
        ip_address=application.telemetry.ip_address,
        annual_income=application.annual_income,
        loan_amount=application.loan_amount,
        status="PENDING",
    )
    database.add(evaluation)
    database.commit()
    background_tasks.add_task(
        request.app.state.fraud_service.process_evaluation_task,
        tracking_id,
        application,
    )
    return AsyncEvaluationResponse(tracking_id=tracking_id, status="PENDING")


@router.get(
    "/status/{tracking_id}",
    response_model=EvaluationStatusResponse,
    dependencies=[Depends(verify_api_key)],
)
async def evaluation_status(
    tracking_id: str,
    database: Session = Depends(get_db),
) -> EvaluationStatusResponse:
    """Return the current state and completed decision for a queued evaluation."""
    evaluation = database.scalar(
        select(EvaluationLog).where(EvaluationLog.tracking_id == tracking_id)
    )
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")
    decision = (
        FraudAssessmentResponse.model_validate(json.loads(evaluation.decision_payload))
        if evaluation.decision_payload
        else None
    )
    return EvaluationStatusResponse(
        tracking_id=evaluation.tracking_id,
        status=evaluation.status,
        evaluation_id=evaluation.id,
        risk_score=evaluation.risk_score,
        risk_level=evaluation.risk_level,
        decision=decision,
    )