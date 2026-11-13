"""Redis-backed rate limiting middleware for sensitive endpoints."""

import time

try:
    from redis.asyncio import Redis
except ImportError:
    class Redis:  # type: ignore[no-redef]
        @classmethod
        def from_url(cls, *args, **kwargs):
            return None
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from purecast.core.config import get_settings
from purecast.core.errors import create_problem_response
from purecast.core.logging import get_logger

logger = get_logger("rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce rate limits on authentication endpoints."""

    def __init__(self, app: object, redis_client: Redis | None = None) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._redis = redis_client

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()

        # Only rate limit auth endpoints
        if not request.url.path.startswith("/api/v1/auth/") or Redis is None:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:auth:{client_ip}:{int(time.time() // 60)}"

        try:
            if self._redis is None:
                self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

            current_count = await self._redis.incr(key)
            if current_count == 1:
                await self._redis.expire(key, 60)

            if current_count > settings.RATE_LIMIT_PER_MINUTE:
                logger.warning(
                    "Rate limit exceeded for auth", client_ip=client_ip, count=current_count
                )
                return create_problem_response(
                    status_code=429,
                    title="Rate Limit Exceeded",
                    detail=(
                        f"Too many authentication attempts. "
                        f"Limit is {settings.RATE_LIMIT_PER_MINUTE} per minute."
                    ),
                    type_slug="rate-limit-exceeded",
                    instance=request.url.path,
                )
        except Exception as e:
            # Fail open if Redis is unavailable
            logger.debug("Redis rate limiting skipped (unavailable)", error=str(e))

        return await call_next(request)
