"""FastAPI application factory, lifespan, and configuration."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from purecast import __version__
from purecast.api.middleware.rate_limit import RateLimitMiddleware
from purecast.api.middleware.request_id import RequestIdMiddleware
from purecast.api.v1 import api_v1_router
from purecast.api.v1.routers.health import router as health_router
from purecast.core.config import get_settings
from purecast.core.errors import register_error_handlers
from purecast.core.logging import get_logger, setup_logging

logger = get_logger("app")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager."""
    settings = get_settings()
    setup_logging(log_level=settings.LOG_LEVEL, json_format=not settings.DEBUG)
    logger.info("Starting PureCast API server", version=__version__, env=settings.APP_ENV)
    yield
    logger.info("Shutting down PureCast API server")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="PureCast API",
        description=(
            "Filter-health forecasting platform for water purifiers. "
            "Multi-tenant advisory backend forecasting remaining filter life from sensor telemetry."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Register custom RFC 7807 error handlers
    register_error_handlers(app)

    # Middleware: Request ID and Rate Limiting
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health and version routers
    app.include_router(health_router)

    # Backward-compatible health probes for phase 0 scaffold tests
    @app.get("/health", tags=["system"], include_in_schema=False)
    async def legacy_health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/ready", tags=["system"], include_in_schema=False)
    async def legacy_ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/", tags=["system"], include_in_schema=False)
    async def root() -> dict[str, Any]:
        return {
            "service": "PureCast API",
            "version": __version__,
            "docs": "/docs",
        }

    # API v1 routes
    app.include_router(api_v1_router)

    return app


# The application instance used by uvicorn
app: FastAPI = create_app()


def run() -> None:
    """Entry point for console_scripts."""
    uvicorn.run(
        "purecast.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
