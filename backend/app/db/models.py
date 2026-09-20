"""SQLAlchemy models for fraud decision audit records."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class FraudAuditLog(Base):
    """Immutable record of a fraud evaluation and its model inputs."""

    __tablename__ = "fraud_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    applicant_id: Mapped[str] = mapped_column(String, nullable=False)
    device_fingerprint_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String, nullable=False)
    risk_factors: Mapped[str] = mapped_column(String, nullable=False)
    feature_vector: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
