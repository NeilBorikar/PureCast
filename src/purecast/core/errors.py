"""Custom exceptions and RFC 7807 Problem Details error handlers."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from purecast.core.logging import get_logger

logger = get_logger("errors")


class PureCastError(Exception):
    """Base application exception."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    title: str = "Internal Server Error"
    type_slug: str = "internal-error"

    def __init__(
        self, detail: str = "An unexpected error occurred", extra: dict[str, Any] | None = None
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.extra = extra or {}


class NotFoundError(PureCastError):
    status_code = status.HTTP_404_NOT_FOUND
    title = "Resource Not Found"
    type_slug = "not-found"


class AuthenticationError(PureCastError):
    status_code = status.HTTP_401_UNAUTHORIZED
    title = "Authentication Failed"
    type_slug = "unauthorized"


class PermissionDeniedError(PureCastError):
    status_code = status.HTTP_403_FORBIDDEN
    title = "Permission Denied"
    type_slug = "forbidden"


class ConflictError(PureCastError):
    status_code = status.HTTP_409_CONFLICT
    title = "Conflict"
    type_slug = "conflict"


class ValidationError(PureCastError):
    status_code = 422
    title = "Validation Error"
    type_slug = "validation-error"


class TenantMismatchError(PureCastError):
    status_code = status.HTTP_403_FORBIDDEN
    title = "Cross-Tenant Access Prohibited"
    type_slug = "tenant-mismatch"


class RateLimitExceededError(PureCastError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    title = "Rate Limit Exceeded"
    type_slug = "rate-limit-exceeded"


def create_problem_response(
    status_code: int,
    title: str,
    detail: str,
    type_slug: str,
    instance: str,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build an RFC 7807 problem+json response."""
    content: dict[str, Any] = {
        "type": f"https://purecast.io/errors/{type_slug}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
    }
    if extra:
        content["invalid_params"] = extra
    return JSONResponse(
        status_code=status_code,
        content=content,
        media_type="application/problem+json",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all RFC 7807 exception handlers on the FastAPI application."""

    @app.exception_handler(PureCastError)
    async def purecast_error_handler(request: Request, exc: PureCastError) -> JSONResponse:
        logger.warning(
            "Application error",
            error_type=exc.type_slug,
            status=exc.status_code,
            detail=exc.detail,
            path=str(request.url.path),
        )
        return create_problem_response(
            status_code=exc.status_code,
            title=exc.title,
            detail=exc.detail,
            type_slug=exc.type_slug,
            instance=str(request.url.path),
            extra=exc.extra,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = str(exc.detail) if exc.detail else "HTTP error"
        return create_problem_response(
            status_code=exc.status_code,
            title="HTTP Error",
            detail=detail,
            type_slug="http-error",
            instance=str(request.url.path),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        return create_problem_response(
            status_code=422,
            title="Validation Error",
            detail="Request body or parameters failed schema validation",
            type_slug="validation-error",
            instance=str(request.url.path),
            extra={"errors": errors},  # type: ignore[dict-item]
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception", path=str(request.url.path), error=str(exc))
        return create_problem_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail="An unexpected internal server error occurred",
            type_slug="internal-server-error",
            instance=str(request.url.path),
        )
