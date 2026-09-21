"""Aggregate fraud evaluation metrics for operational dashboards."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.db.models import FraudAuditLog


router = APIRouter()


@router.get("/metrics")
def get_metrics() -> dict[str, int | float | dict[str, int]]:
	"""Return aggregate counts from persisted fraud evaluation audit logs."""
	with SessionLocal() as database:
		total_evaluations = database.scalar(
			select(func.count()).select_from(FraudAuditLog)
		) or 0
		high_risk_evaluations = database.scalar(
			select(func.count())
			.select_from(FraudAuditLog)
			.where(FraudAuditLog.risk_level == "HIGH")
		) or 0
		risk_distribution = {
			risk_level: database.scalar(
				select(func.count())
				.select_from(FraudAuditLog)
				.where(FraudAuditLog.risk_level == risk_level)
			) or 0
			for risk_level in ("HIGH", "MEDIUM", "LOW")
		}
		repeat_offenders_blocked = database.scalar(
			select(func.count())
			.select_from(FraudAuditLog)
			.where(FraudAuditLog.risk_factors.like("%Repeat offender%"))
		) or 0

	return {
		"total_evaluations": total_evaluations,
		"fraud_rate_pct": round(
			(high_risk_evaluations / total_evaluations * 100)
			if total_evaluations
			else 0.0,
			2,
		),
		"risk_distribution": risk_distribution,
		"repeat_offenders_blocked": repeat_offenders_blocked,
	}