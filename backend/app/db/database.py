"""Database configuration and session dependencies."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings


DATABASE_URL = settings.DATABASE_URL
engine_kwargs = (
    {"connect_args": {"check_same_thread": False}}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and always close it afterward."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


def init_db() -> None:
    """Create all registered database tables if they do not exist."""
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
