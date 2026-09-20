"""FastAPI application entrypoint for the fraud detection API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as fraud_router
from app.core.config import settings


app = FastAPI(
	title=settings.APP_NAME,
	version=settings.VERSION,
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:3000"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(fraud_router, prefix="/api/v1/fraud")


@app.get("/health")
def health_check() -> dict[str, str]:
	"""Return the current API health status."""
	return {"status": "healthy"}
