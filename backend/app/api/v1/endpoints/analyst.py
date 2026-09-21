"""Analyst review and decision override endpoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.database import get_db
from app.db.models import AuditLog, EvaluationLog
from app.models.schemas import AnalystOverrideRequest

router = APIRouter(prefix="/analyst", dependencies=[Depends(verify_api_key)])


@router.get("/pending-reviews")
async def pending_reviews(database: Session = Depends(get_db)) -> list[dict]:
    """Return completed MEDIUM and HIGH evaluations for analyst review."""
    evaluations = database.scalars(
        select(EvaluationLog)
        .where(
            EvaluationLog.status == "COMPLETED",
            EvaluationLog.risk_level.in_(("MEDIUM", "HIGH")),
        )
        .order_by(EvaluationLog.created_at.desc())
    ).all()
    return [
        {
            "evaluation_id": evaluation.id,
            "tracking_id": evaluation.tracking_id,
            "user_id": evaluation.user_id,
            "device_id": evaluation.device_id,
            "risk_score": evaluation.risk_score,
            "risk_level": evaluation.risk_level,
            "created_at": evaluation.created_at.isoformat(),
        }
        for evaluation in evaluations
    ]


@router.post("/override", status_code=status.HTTP_200_OK)
async def override_evaluation(
    override: AnalystOverrideRequest,
    database: Session = Depends(get_db),
) -> dict:
    """Record an analyst override and update the evaluation decision."""
    evaluation = database.get(EvaluationLog, override.evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")

    previous_decision = evaluation.risk_level or evaluation.status
    audit = AuditLog(
        id=str(uuid4()),
        evaluation_id=evaluation.id,
        analyst_id=override.analyst_id,
        previous_decision=previous_decision,
        new_decision=override.new_decision,
        reason=override.reason,
        created_at=datetime.now(timezone.utc),
    )
    evaluation.risk_level = override.new_decision
    database.add(audit)
    database.commit()
    database.refresh(evaluation)
    return {
        "evaluation_id": evaluation.id,
        "tracking_id": evaluation.tracking_id,
        "previous_decision": previous_decision,
        "new_decision": evaluation.risk_level,
        "reason": override.reason,
        "status": evaluation.status,
    }