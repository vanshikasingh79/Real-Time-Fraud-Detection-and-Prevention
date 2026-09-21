"""Tests for the runtime health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_connected_database_and_response_time() -> None:
	"""The health endpoint reports database availability and request latency."""
	with TestClient(app) as client:
		response = client.get("/api/v1/health")

	assert response.status_code == 200
	assert response.json()["database"] == "connected"
	assert response.headers["X-Response-Time-MS"]