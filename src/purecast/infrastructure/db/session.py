"""Async database session and engine management."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from purecast.core.config import get_settings


def create_engine_and_session(
    url: str | None = None,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    settings = get_settings()
    db_url = url or settings.DATABASE_URL

    if "sqlite" in db_url:
        engine = create_async_engine(
            db_url,
            echo=settings.DATABASE_ECHO,
        )
    else:
        engine = create_async_engine(
            db_url,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
            echo=settings.DATABASE_ECHO,
        )

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, session_factory


engine, async_session_factory = create_engine_and_session()


async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependency for obtaining an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
