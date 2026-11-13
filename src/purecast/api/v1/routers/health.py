"""Health check and service status endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from purecast import __version__
from purecast.core.config import get_settings
from purecast.core.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health/live", summary="Liveness Probe")
async def liveness() -> dict[str, str]:
    """Liveness probe: verifies process is running."""
    return {"status": "alive"}


@router.get("/health/ready", summary="Readiness Probe")
async def readiness(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Readiness probe: validates database and cache connectivity."""
    db_ok = False
    redis_ok = False
    details: dict[str, str] = {}

    # Check database
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
        details["database"] = "connected"
    except Exception as e:
        details["database"] = f"unhealthy: {e!s}"

    # Check redis
    settings = get_settings()
    try:
        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        await redis_client.aclose()
        redis_ok = True
        details["redis"] = "connected"
    except Exception as e:
        details["redis"] = f"unhealthy: {e!s}"

    # Allow db-only readiness in development when redis container is not present
    is_ready = db_ok and (redis_ok or settings.APP_ENV == "development")

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "components": details}

    return {"status": "ready", "components": details}


@router.get("/version", summary="Version Info")
async def version() -> dict[str, str]:
    """Returns application name and semver version."""
    return {
        "service": "PureCast API",
        "version": __version__,
    }
