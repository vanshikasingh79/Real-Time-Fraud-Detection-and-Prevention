"""SQLAlchemy models for fraud decision audit records."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
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


class EvaluationLog(Base):
    """Track synchronous or background evaluation lifecycle state."""

    __tablename__ = "evaluation_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tracking_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String, index=True, nullable=False)
    annual_income: Mapped[float] = mapped_column(Float, nullable=False)
    loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    decision_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AuditLog(Base):
    """Immutable analyst decision override record."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_logs.id"), index=True, nullable=False
    )
    analyst_id: Mapped[str] = mapped_column(String, nullable=False)
    previous_decision: Mapped[str] = mapped_column(String, nullable=False)
    new_decision: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
