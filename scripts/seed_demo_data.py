"""Seed realistic demo applications into a running Fraud Guard API."""

from __future__ import annotations

import os
import time
from collections import Counter
from typing import Any

import httpx

DEFAULT_API_URL = "http://localhost:8000/api/v1"
DEFAULT_API_KEY = "fg-sk-dev-hackathon-key-2026"
REPEAT_OFFENDER_FINGERPRINT = "DEMO-REPEAT-OFFENDER-001"


def application_payload(
    index: int,
    loan_amount: int,
    annual_income: int,
    telemetry: dict[str, Any],
) -> dict[str, Any]:
    """Build a valid application with unique applicant and device identifiers."""
    return {
        "applicant_id": f"demo-applicant-{index:03d}",
        "loan_amount": loan_amount,
        "annual_income": annual_income,
        "requested_term_months": 36,
        "telemetry": {
            "ip_address": f"198.51.100.{index}",
            "device_fingerprint_id": f"DEMO-DEVICE-{index:03d}",
            "session_id": f"demo-session-{index:03d}",
            **telemetry,
        },
    }


APPLICATIONS = [
    *[
        application_payload(
            index,
            loan_amount,
            annual_income,
            {
                "typing_speed_wpm": typing_speed,
                "paste_event_count": 0,
                "mouse_jitter_score": jitter,
                "session_duration_seconds": duration,
                "is_vpn": False,
            },
        )
        for index, loan_amount, annual_income, typing_speed, jitter, duration in [
            (1, 8000, 72000, 48, 0.42, 240),
            (2, 12000, 85000, 62, 0.36, 310),
            (3, 18000, 110000, 55, 0.51, 420),
            (4, 22000, 125000, 71, 0.31, 275),
            (5, 9500, 64000, 44, 0.47, 195),
            (6, 30000, 145000, 58, 0.39, 360),
            (7, 15000, 92000, 67, 0.55, 225),
            (8, 27000, 130000, 52, 0.34, 290),
            (9, 6000, 58000, 39, 0.61, 260),
            (10, 35000, 180000, 76, 0.44, 480),
            (11, 14000, 78000, 57, 0.28, 205),
            (12, 24000, 118000, 63, 0.49, 330),
            (13, 11000, 70000, 46, 0.37, 185),
            (14, 42000, 210000, 69, 0.58, 390),
            (15, 20000, 105000, 53, 0.46, 315),
        ]
    ],
    *[
        application_payload(
            index,
            loan_amount,
            annual_income,
            {
                "typing_speed_wpm": typing_speed,
                "paste_event_count": paste_count,
                "mouse_jitter_score": jitter,
                "session_duration_seconds": duration,
                "is_vpn": is_vpn,
            },
        )
        for index, loan_amount, annual_income, typing_speed, paste_count, jitter, duration, is_vpn in [
            (16, 42000, 65000, 132, 2, 0.12, 95, False),
            (17, 28000, 46000, 18, 1, 0.08, 70, False),
            (18, 55000, 90000, 108, 4, 0.21, 130, False),
            (19, 16000, 30000, 82, 3, 0.06, 55, True),
            (20, 70000, 125000, 145, 2, 0.17, 110, False),
            (21, 36000, 60000, 24, 5, 0.11, 85, True),
        ]
    ],
    *[
        application_payload(
            index,
            loan_amount,
            annual_income,
            {
                "typing_speed_wpm": typing_speed,
                "paste_event_count": paste_count,
                "mouse_jitter_score": jitter,
                "session_duration_seconds": duration,
                "is_vpn": is_vpn,
            },
        )
        for index, loan_amount, annual_income, typing_speed, paste_count, jitter, duration, is_vpn in [
            (22, 90000, 42000, 220, 12, 0.01, 18, True),
            (23, 65000, 30000, 190, 9, 0.02, 22, True),
            (24, 120000, 55000, 175, 15, 0.0, 15, True),
            (25, 48000, 25000, 205, 11, 0.03, 25, True),
        ]
    ],
]

REPEAT_OFFENDER_APPLICATIONS = [
    {
        "applicant_id": "demo-repeat-offender-001-a",
        "loan_amount": 85000,
        "annual_income": 35000,
        "requested_term_months": 24,
        "telemetry": {
            "typing_speed_wpm": 240,
            "paste_event_count": 18,
            "mouse_jitter_score": 0.0,
            "session_duration_seconds": 12,
            "ip_address": "203.0.113.41",
            "device_fingerprint_id": REPEAT_OFFENDER_FINGERPRINT,
            "session_id": "repeat-session-a",
            "is_vpn": True,
        },
    },
    {
        "applicant_id": "demo-repeat-offender-001-b",
        "loan_amount": 92000,
        "annual_income": 40000,
        "requested_term_months": 24,
        "telemetry": {
            "typing_speed_wpm": 230,
            "paste_event_count": 20,
            "mouse_jitter_score": 0.01,
            "session_duration_seconds": 10,
            "ip_address": "203.0.113.42",
            "device_fingerprint_id": REPEAT_OFFENDER_FINGERPRINT,
            "session_id": "repeat-session-b",
            "is_vpn": True,
        },
    },
]


def main() -> None:
    api_url = os.getenv("DEMO_API_URL", DEFAULT_API_URL).rstrip("/")
    api_key = os.getenv("DEMO_API_KEY", DEFAULT_API_KEY)
    endpoint = f"{api_url}/fraud/evaluate"
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    risk_counts: Counter[str] = Counter()
    submitted = 0

    with httpx.Client(headers=headers, timeout=30.0) as client:
        for payload in [*APPLICATIONS, *REPEAT_OFFENDER_APPLICATIONS]:
            try:
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
                body = response.json()
                risk_counts[body.get("risk_level", "UNKNOWN")] += 1
                submitted += 1
                print(f"Submitted {payload['applicant_id']}: {body.get('risk_level', 'UNKNOWN')}")
            except (httpx.HTTPError, ValueError) as exc:
                print(f"Failed {payload['applicant_id']}: {exc}")
            time.sleep(0.2)

    print("\nDemo seed summary")
    print(f"Total submitted: {submitted}")
    for risk_level in ("LOW", "MEDIUM", "HIGH", "UNKNOWN"):
        if risk_counts[risk_level] or risk_level != "UNKNOWN":
            print(f"{risk_level}: {risk_counts[risk_level]}")
    print(
        "REPEAT OFFENDER DEMO FINGERPRINT (use this in the live demo): "
        f"{REPEAT_OFFENDER_FINGERPRINT}"
    )


if __name__ == "__main__":
    main()
