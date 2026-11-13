"""FastAPI dependencies: database session, authentication, RBAC, and pagination."""

from dataclasses import dataclass
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, Header, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.api.v1.permissions import has_permission
from purecast.core.errors import AuthenticationError, PermissionDeniedError
from purecast.core.security import decode_token, hash_api_key
from purecast.domain.enums import Role
from purecast.infrastructure.db.models import ApiKey, User
from purecast.infrastructure.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@dataclass
class PaginationParams:
    """Pagination query parameters."""

    skip: int = 0
    limit: int = 20


def get_pagination(
    skip: Annotated[int, Query(ge=0, description="Offset")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
) -> PaginationParams:
    """Extract pagination parameters."""
    return PaginationParams(skip=skip, limit=limit)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
) -> User:
    """Resolve current user from JWT access token or API Key."""
    if token:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Token missing subject")

        try:
            user_id = UUID(user_id_str)
        except ValueError as err:
            raise AuthenticationError("Invalid user ID in token") from err

        result = await session.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        return user

    if x_api_key:
        hashed = hash_api_key(x_api_key)
        result = await session.execute(select(ApiKey).filter(ApiKey.key_hash == hashed))
        api_key_obj = result.scalars().first()
        if not api_key_obj or not api_key_obj.is_active:
            raise AuthenticationError("Invalid or inactive API Key")

        # Return a synthetic User for the API key caller
        return User(
            id=api_key_obj.id,
            tenant_id=api_key_obj.tenant_id,
            email=f"{api_key_obj.name}@api-key.purecast",
            hashed_password="",
            full_name=api_key_obj.name,
            role=api_key_obj.role,
            is_active=True,
        )

    raise AuthenticationError("Authentication required (Bearer token or X-API-Key)")


def require_roles(*allowed_roles: Role | str) -> Any:
    """Dependency factory checking user against a set of allowed roles."""
    normalized_roles = {Role(r).value if isinstance(r, str) else r.value for r in allowed_roles}
    # Platform admin always has access
    normalized_roles.add(Role.PLATFORM_ADMIN.value)

    async def _role_checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in normalized_roles:
            raise PermissionDeniedError(
                f"Role '{user.role}' does not have sufficient permissions for this operation"
            )
        return user

    return _role_checker


def require_permission(permission: str) -> Any:
    """Dependency factory checking user against specific granular permission."""

    async def _perm_checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if not has_permission(user.role, permission):
            raise PermissionDeniedError(f"Missing required permission: {permission}")
        return user

    return _perm_checker
