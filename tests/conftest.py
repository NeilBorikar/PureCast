"""Pytest global configuration and fixtures."""

import contextlib
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from purecast.core.config import get_settings
from purecast.infrastructure.db.models import Base
from purecast.infrastructure.db.session import get_db
from purecast.main import app

# Ensure testing settings
settings = get_settings()
settings.TESTING = True
settings.APP_ENV = "test"

TEST_DB_PATH = Path("./test_purecast.db").resolve()
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
)
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
async def init_test_db() -> AsyncIterator[None]:
    """Initialize database tables before test suite and drop after."""
    # Delete old test DB if left over
    if TEST_DB_PATH.exists():
        with contextlib.suppress(Exception):
            TEST_DB_PATH.unlink()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

    if TEST_DB_PATH.exists():
        with contextlib.suppress(Exception):
            TEST_DB_PATH.unlink()


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide an isolated database session for a test."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Provide an AsyncClient wired to the FastAPI application with test database."""

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
