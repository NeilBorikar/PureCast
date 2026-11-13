"""API v1 router combining all resource endpoints."""

from fastapi import APIRouter

from purecast import __version__
from purecast.api.v1.routers.analyze import router as analyze_router
from purecast.api.v1.routers.auth import router as auth_router
from purecast.api.v1.routers.devices import router as devices_router
from purecast.api.v1.routers.health import router as health_router
from purecast.api.v1.routers.households import router as households_router
from purecast.api.v1.routers.tenants import router as tenants_router
from purecast.api.v1.routers.users import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")

@api_v1_router.get("/health", tags=["health"])
async def api_health() -> dict[str, str]:
    return {"status": "healthy", "version": __version__}

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(tenants_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(households_router)
api_v1_router.include_router(devices_router)
api_v1_router.include_router(analyze_router)

__all__ = ["api_v1_router"]
