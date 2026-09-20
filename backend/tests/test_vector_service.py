"""Tests for historical fraud-case vector similarity search."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import FraudAuditLog
from app.services.vector_service import VectorSimilarityEngine


def test_identical_vectors_match_and_low_similarity_is_ignored() -> None:
    """Identical vectors score 1.0 while orthogonal vectors are filtered out."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as database:
        database.add_all(
            [
                FraudAuditLog(
                    application_id="identical-case",
                    applicant_id="applicant-1",
                    device_fingerprint_id="device-1",
                    ip_address="192.168.x.x",
                    risk_score=0.8,
                    risk_level="HIGH",
                    recommended_action="BLOCK",
                    risk_factors=json.dumps(["VPN usage"]),
                    feature_vector=json.dumps([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
                    timestamp=datetime.now(timezone.utc),
                ),
                FraudAuditLog(
                    application_id="orthogonal-case",
                    applicant_id="applicant-2",
                    device_fingerprint_id="device-2",
                    ip_address="192.168.x.x",
                    risk_score=0.4,
                    risk_level="MEDIUM",
                    recommended_action="STEP_UP_AUTHENTICATION",
                    risk_factors=json.dumps(["Paste activity"]),
                    feature_vector=json.dumps([0.0, 1.0, 0.0, 0.0, 0.0, 0.0]),
                    timestamp=datetime.now(timezone.utc),
                ),
            ]
        )
        database.commit()

        matches = VectorSimilarityEngine().find_similar_cases(
            database,
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            min_similarity=0.80,
        )

    assert len(matches) == 1
    assert matches[0]["application_id"] == "identical-case"
    assert matches[0]["similarity_score"] == 1.0
