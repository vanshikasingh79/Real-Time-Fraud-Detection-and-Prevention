"""Historical fraud-case similarity search using NumPy cosine similarity."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FraudAuditLog


class VectorSimilarityEngine:
    """Find historically similar medium- and high-risk audit cases."""

    def find_similar_cases(
        self,
        db: Session,
        current_vector: list[float],
        top_k: int = 3,
        min_similarity: float = 0.80,
    ) -> list[dict]:
        """Return recent flagged cases whose cosine similarity meets the threshold."""
        if top_k <= 0 or not current_vector:
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        records = db.scalars(
            select(FraudAuditLog).where(
                FraudAuditLog.risk_level.in_(("MEDIUM", "HIGH")),
                FraudAuditLog.timestamp >= cutoff,
            )
        ).all()
        if not records:
            return []

        current = np.asarray(current_vector, dtype=float)
        current_norm = np.linalg.norm(current)
        if current.ndim != 1 or current_norm == 0:
            return []
        current = current / current_norm

        matches: list[dict] = []
        for record in records:
            try:
                historical = np.asarray(json.loads(record.feature_vector), dtype=float)
                if historical.ndim != 1 or historical.shape != current.shape:
                    continue
                historical_norm = np.linalg.norm(historical)
                if historical_norm == 0:
                    continue
                similarity = float(np.dot(current, historical / historical_norm))
                if similarity >= min_similarity:
                    matches.append(
                        {
                            "application_id": record.application_id,
                            "risk_level": record.risk_level,
                            "risk_factors": json.loads(record.risk_factors),
                            "similarity_score": similarity,
                        }
                    )
            except (TypeError, ValueError, json.JSONDecodeError):
                continue

        matches.sort(key=lambda match: match["similarity_score"], reverse=True)
        return matches[:top_k]
