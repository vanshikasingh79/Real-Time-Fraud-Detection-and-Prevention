"""Responsible AI guardrails for prompt sanitization and explanation grounding."""

from __future__ import annotations

import hashlib
import re
from typing import List

from app.models.schemas import AIExplanation, LoanApplicationRequest


class AIGuardrailService:
    """Protect sensitive application data and validate AI explanation grounding."""

    _IGNORED_TERMS = {
        "a",
        "an",
        "and",
        "detected",
        "for",
        "high",
        "low",
        "medium",
        "of",
        "possible",
        "score",
        "the",
        "to",
        "within",
    }

    def sanitize_payload(self, application: LoanApplicationRequest) -> dict:
        """Return an application dictionary with identifying values redacted.

        Applicant identifiers are replaced with a fixed anonymous value. IPv4
        addresses retain only their first two octets, while other address formats
        are replaced entirely. Device fingerprints are represented by a stable,
        shortened hash that cannot expose the original identifier.
        """
        payload = application.model_dump()
        payload["applicant_id"] = "ANONYMIZED_APPLICANT"
        telemetry = payload["telemetry"]
        telemetry["ip_address"] = self._mask_ip_address(telemetry["ip_address"])
        telemetry["device_fingerprint_id"] = self._mask_device_id(
            telemetry["device_fingerprint_id"]
        )
        return payload

    @staticmethod
    def _mask_ip_address(ip_address: str) -> str:
        """Mask an IPv4 address while fully redacting other address formats."""
        octets = ip_address.split(".")
        if len(octets) == 4 and all(octet.isdigit() for octet in octets):
            return f"{octets[0]}.{octets[1]}.x.x"
        return "ANONYMIZED_IP"

    @staticmethod
    def _mask_device_id(device_id: str) -> str:
        """Return a stable non-reversible device fingerprint representation."""
        digest = hashlib.sha256(device_id.encode("utf-8")).hexdigest().upper()
        return f"DEV-***-{digest[-3:]}"

    def verify_grounding(
        self,
        explanation: AIExplanation,
        model_risk_factors: List[str],
    ) -> bool:
        """Check that every explanation point is supported by model risk factors.

        Each justification point must share at least one meaningful term with a
        model-provided factor. This rejects unsupported claims such as credit
        history failures when the model only observed telemetry signals.
        """
        if not explanation.is_grounded or not explanation.risk_justification_points:
            return False
        if not model_risk_factors:
            return False

        model_terms = {
            term
            for factor in model_risk_factors
            for term in self._meaningful_terms(factor)
        }
        return all(
            self._meaningful_terms(point) & model_terms
            for point in explanation.risk_justification_points
        )

    @classmethod
    def _meaningful_terms(cls, text: str) -> set[str]:
        """Extract normalized, non-generic terms used for grounding checks."""
        terms = set(re.findall(r"[a-z0-9]+", text.lower()))
        return terms - cls._IGNORED_TERMS
