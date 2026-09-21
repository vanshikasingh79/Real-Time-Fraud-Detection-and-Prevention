"""Tests for the aggregate metrics endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_metrics_returns_expected_keys() -> None:
	"""The metrics endpoint returns all dashboard aggregate fields."""
	with TestClient(app) as client:
		response = client.get("/api/v1/metrics")

	assert response.status_code == 200
	body = response.json()
	assert {
		"total_evaluations",
		"fraud_rate_pct",
		"risk_distribution",
		"repeat_offenders_blocked",
	}.issubset(body)
	assert set(body["risk_distribution"]) == {"HIGH", "MEDIUM", "LOW"}