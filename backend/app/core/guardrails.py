"""Responsible AI guardrails for prompt sanitization and grounding."""

from __future__ import annotations

import hashlib
import ipaddress
import re

from app.models.schemas import LoanApplicationRequest


class AIGuardrailService:
    """Protect sensitive application data and validate AI explanation grounding."""

    _IGNORED_TERMS = {
        "a", "an", "and", "detected", "for", "high", "low", "medium",
        "of", "possible", "score", "the", "to", "within",
    }

    def sanitize_payload(self, application: LoanApplicationRequest) -> dict:
        """Return an application dictionary with identifying values redacted."""
        payload = application.model_dump()
        payload["applicant_id"] = "ANONYMIZED_APPLICANT"
        telemetry = payload["telemetry"]
        telemetry["ip_address"] = self._mask_ip_address(telemetry["ip_address"])
        telemetry["device_id"] = self._mask_device_id(
            telemetry["device_id"]
        )
        return payload

    @staticmethod
    def _mask_ip_address(ip_address: str) -> str:
        """Mask the host portion of an IPv4 or IPv6 address."""
        try:
            address = ipaddress.ip_address(ip_address)
        except ValueError:
            return "ANONYMIZED_IP"

        if address.version == 4:
            octets = ip_address.split(".")
            return f"{octets[0]}.{octets[1]}.x.x"

        hextets = address.exploded.split(":")
        return ":".join(hextets[:2] + ["x"] * 6)

    @staticmethod
    def _mask_device_id(device_id: str) -> str:
        """Return a masked device fingerprint while retaining three characters."""
        visible_suffix = re.sub(r"[^A-Za-z0-9]", "", device_id)[-3:]
        if len(visible_suffix) < 3:
            visible_suffix = hashlib.sha256(device_id.encode("utf-8")).hexdigest()[-3:].upper()
        return f"DEV-***-{visible_suffix}"

    def verify_grounding(
        self,
        explanation_justifications: list[str],
        model_risk_factors: list[str],
    ) -> bool:
        """Check that every explanation point maps to a model risk factor."""
        if not explanation_justifications or not model_risk_factors:
            return False
        model_terms = {
            term for factor in model_risk_factors for term in self._meaningful_terms(factor)
        }
        return all(
            self._meaningful_terms(point) & model_terms
            for point in explanation_justifications
        )

    @classmethod
    def _meaningful_terms(cls, text: str) -> set[str]:
        """Extract normalized terms used for grounding checks."""
        return set(re.findall(r"[a-z0-9]+", text.lower())) - cls._IGNORED_TERMS