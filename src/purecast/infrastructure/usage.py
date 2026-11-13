'''Infrastructure for usage metering and feature flags.'''

from datetime import datetime, UTC
from typing import Any

import redis.asyncio as aioredis
from purecast.core.config import Settings

# Global redis connection (lazy)
_redis: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = Settings()
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis

async def increment_metric(tenant_id: str, metric: str, amount: int = 1) -> None:
    """Increment a usage counter for a tenant.
    Counters are stored as Redis hash fields: `usage:{tenant_id}`.
    """
    redis = await get_redis()
    await redis.hincrby(f"usage:{tenant_id}", metric, amount)

async def get_metric(tenant_id: str, metric: str) -> int:
    redis = await get_redis()
    val = await redis.hget(f"usage:{tenant_id}", metric)
    return int(val) if val else 0

# Feature flag mapping (static for MVP)
# plan_name -> set of feature identifiers
FEATURE_FLAGS = {
    "LITE": set(),
    "FULL": {"fleet_analytics", "ml_forecast", "orders", "service_requests"},
    "ENTERPRISE": {"fleet_analytics", "ml_forecast", "orders", "service_requests", "api_access", "sla"},
}

async def require_feature(plan_name: str, feature: str):
    """Dependency that checks if the tenant's plan includes the feature.
    Returns None on success, raises HTTPException on failure.
    """
    from fastapi import HTTPException, status
    if feature not in FEATURE_FLAGS.get(plan_name, set()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Feature '{feature}' not available for plan '{plan_name}'.",
        )
    return None

