"""End-to-end smoke test for the running Fraud Guard API."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Any

import httpx


# Use the IPv4 loopback explicitly: on Windows, ``localhost`` may try an
# unbound IPv6 loopback first and add seconds to every first request.
API_URL = "http://127.0.0.1:8000/api/v1/fraud/evaluate?include_explanation=true"


@dataclass(frozen=True)
class Scenario:
    """A named request profile and its expected production decision."""

    name: str
    typing_speed_wpm: float
    paste_event_count: int
    mouse_jitter_score: float
    is_vpn: bool
    loan_amount: float
    expected_level: str
    expected_action: str


SCENARIOS = (
    Scenario("A - Low Risk", 65, 0, 0.85, False, 10_000, "LOW", "APPROVE"),
    Scenario(
        "B - Medium Risk", 10, 3, 0.4, False, 30_000,
        "MEDIUM", "STEP_UP_AUTHENTICATION",
    ),
    Scenario(
        "C - High Risk - Bot Attack", 190, 7, 0.01, True, 70_000,
        "HIGH", "BLOCK",
    ),
)


def payload_for(scenario: Scenario) -> dict[str, Any]:
    """Build a valid API payload for a smoke-test scenario."""
    return {
        "applicant_id": scenario.name,
        "loan_amount": scenario.loan_amount,
        "annual_income": 100_000,
        "requested_term_months": 24,
        "telemetry": {
            "typing_speed_wpm": scenario.typing_speed_wpm,
            "paste_event_count": scenario.paste_event_count,
            "mouse_jitter_score": scenario.mouse_jitter_score,
            "session_duration_seconds": 45,
            "ip_address": "192.168.1.1",
            "device_fingerprint_id": "DEV-SMOKE-001",
            "is_vpn": scenario.is_vpn,
        },
    }


def run_scenario(client: httpx.Client, scenario: Scenario) -> list[str]:
    """Execute one scenario and return any validation failures."""
    failures: list[str] = []
    started = time.perf_counter()
    response = client.post(API_URL, json=payload_for(scenario))
    elapsed_ms = (time.perf_counter() - started) * 1000

    if response.status_code != 200:
        failures.append(f"HTTP {response.status_code}: {response.text}")
        print(f"[FAIL] {scenario.name} - HTTP {response.status_code}")
        return failures

    body = response.json()
    if body.get("risk_level") != scenario.expected_level:
        failures.append(f"expected risk_level={scenario.expected_level}, got {body.get('risk_level')}")
    if body.get("recommended_action") != scenario.expected_action:
        failures.append(f"expected action={scenario.expected_action}, got {body.get('recommended_action')}")
    if elapsed_ms >= 100:
        failures.append(f"expected response_time<100ms, got {elapsed_ms:.1f}ms")

    explanation = body.get("explanation")
    if not explanation:
        failures.append("explanation is missing")
    else:
        if len(explanation.get("plain_english_summary", "")) <= 10:
            failures.append("explanation summary is too short")
        if explanation.get("is_grounded") is not True:
            failures.append("explanation is not grounded")
    if body.get("pii_sanitized") is not True:
        failures.append("pii_sanitized is not true")

    status = "PASS" if not failures else "FAIL"
    print(f"[{status}] {scenario.name} - Response Time: {elapsed_ms:.1f}ms")
    for failure in failures:
        print(f"       {failure}")
    return failures


def main() -> int:
    """Run all smoke scenarios and return a shell-friendly exit code."""
    print("Fraud Guard API smoke test")
    print("=" * 29)
    try:
        with httpx.Client(timeout=5.0) as client:
            failures = [
                failure
                for scenario in SCENARIOS
                for failure in run_scenario(client, scenario)
            ]
    except httpx.HTTPError as exc:
        print(f"[FAIL] API unavailable: {exc}")
        return 1

    print("=" * 29)
    if failures:
        print(f"[FAIL] {len(failures)} assertion(s) failed")
        return 1
    print("[PASS] All smoke checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
