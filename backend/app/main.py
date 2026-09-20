"""FastAPI application entrypoint for the fraud detection API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.services.explainability_service import ExplainabilityEngine
from app.services.fraud_service import FraudEvaluationService


@asynccontextmanager
async def lifespan(application: FastAPI):
	"""Load the fraud model once when the application starts."""
	application.state.fraud_service = FraudEvaluationService(
		explainability_engine=ExplainabilityEngine()
	)
	yield


app = FastAPI(
	title=settings.APP_NAME,
	version=settings.VERSION,
	lifespan=lifespan,
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:3000"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
	"""Return the current API health status."""
	return {"status": "healthy"}
