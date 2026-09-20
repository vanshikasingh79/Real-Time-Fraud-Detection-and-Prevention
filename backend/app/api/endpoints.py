"""Backward-compatible import for the versioned fraud endpoints."""

from app.api.v1.endpoints.fraud import evaluate_application, router

__all__ = ["evaluate_application", "router"]