"""FastAPI application entrypoint for the fraud detection API."""

from __future__ import annotations

from contextlib import asynccontextmanager
import json
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.database import init_db
from app.services.explainability_service import ExplainabilityEngine
from app.services.fraud_service import FraudEvaluationService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
	"""Load the fraud model once when the application starts."""
	application.state.started_at = time.perf_counter()
	init_db()
	application.state.fraud_service = FraudEvaluationService(
		explainability_engine=ExplainabilityEngine()
	)
	yield


app = FastAPI(
	title=settings.APP_NAME,
	version=settings.VERSION,
	lifespan=lifespan,
)
app.state.limiter = limiter


async def rate_limit_exception_handler(
	request: Request,
	exc: RateLimitExceeded,
) -> JSONResponse:
	"""Return a consistent JSON response when a client exceeds its limit."""
	return JSONResponse(
		status_code=429,
		content={"detail": "Rate limit exceeded. Please try again later."},
	)


app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
	CORSMiddleware,
	allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
	"""Log request timing and attach correlation and latency headers."""
	request_id = str(uuid4())
	start_time = time.perf_counter()
	client_ip = request.client.host if request.client else None
	logger.info(
		json.dumps(
			{
				"event": "request_started",
				"request_id": request_id,
				"method": request.method,
				"path": request.url.path,
				"client_ip": client_ip,
			}
		)
	)

	response = await call_next(request)
	latency_ms = (time.perf_counter() - start_time) * 1000
	response.headers["X-Request-ID"] = request_id
	response.headers["X-Response-Time-MS"] = f"{latency_ms:.2f}"
	logger.info(
		json.dumps(
			{
				"event": "request_completed",
				"request_id": request_id,
				"method": request.method,
				"path": request.url.path,
				"status_code": response.status_code,
				"latency_ms": round(latency_ms, 2),
			}
		)
	)
	return response


app.include_router(api_router, prefix="/api/v1")
