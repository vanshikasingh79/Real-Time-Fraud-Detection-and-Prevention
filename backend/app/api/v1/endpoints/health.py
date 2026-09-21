"""Runtime health monitoring endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
import time

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.db.database import engine


router = APIRouter()


@router.get("/health")
def health_check(request: Request) -> dict[str, str | float]:
	"""Return API and database runtime diagnostics."""
	database_status = "connected"
	status = "ok"
	try:
		with engine.connect() as connection:
			connection.execute(text("SELECT 1"))
	except Exception:
		database_status = "disconnected"
		status = "degraded"

	return {
		"status": status,
		"database": database_status,
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"uptime_seconds": round(
			time.perf_counter() - request.app.state.started_at,
			2,
		),
	}