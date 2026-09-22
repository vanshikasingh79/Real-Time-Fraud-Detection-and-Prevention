"""Pytest configuration for backend package imports."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
os.environ.setdefault("API_KEY", "fg-sk-dev-hackathon-key-2026")

from app.core.config import settings
from app.main import app


logger = logging.getLogger(__name__)


@pytest.fixture
def client():
    """Provide an authenticated TestClient for protected endpoint tests."""
    with TestClient(app, headers={"X-API-Key": settings.API_KEY}) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def event_loop():
    """Provide one event loop and close it only after async teardown completes."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.run_until_complete(loop.shutdown_asyncgens())
        if hasattr(loop, "shutdown_default_executor"):
            loop.run_until_complete(loop.shutdown_default_executor())
        loop.close()


async def _wait_for_database_ready() -> None:
    """Wait for PostgreSQL before running tests that use the service."""
    from app.core.config import settings

    database_url = os.getenv("DATABASE_URL", settings.DATABASE_URL).strip()
    if database_url.startswith("sqlite"):
        return

    try:
        from importlib import import_module

        asyncpg = import_module("asyncpg")
    except ImportError as exc:
        raise RuntimeError(
            "PostgreSQL tests require the asyncpg package to be installed."
        ) from exc

    probe_url = settings.async_database_url
    deadline = asyncio.get_running_loop().time() + 15
    delay = 1.0
    last_error: Exception | None = None

    while asyncio.get_running_loop().time() < deadline:
        try:
            connection = await asyncpg.connect(dsn=probe_url)
            await connection.close()
            logger.info("PostgreSQL is ready for the test session")
            return
        except (
            ConnectionRefusedError,
            OSError,
            asyncpg.exceptions.CannotConnectNowError,
        ) as exc:
            last_error = exc
            logger.warning("PostgreSQL is not ready yet: %s", exc)
            remaining = deadline - asyncio.get_running_loop().time()
            await asyncio.sleep(min(delay, max(remaining, 0)))
            delay = min(delay * 2, 4.0)

    raise RuntimeError(
        "PostgreSQL service failed to initialize in CI within timeout window."
    ) from last_error


@pytest.fixture(scope="session", autouse=True)
def wait_for_database_ready() -> None:
    """Run the asynchronous readiness probe without requiring pytest-asyncio."""
    asyncio.run(_wait_for_database_ready())
