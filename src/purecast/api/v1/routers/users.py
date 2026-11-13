"""Tenant-scoped user management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.api.schemas.user import UserCreate, UserResponse, UserRoleUpdate
from purecast.core.deps import PaginationParams, get_db, get_pagination, require_roles
from purecast.core.errors import ConflictError
from purecast.core.security import hash_password
from purecast.domain.enums import Role
from purecast.infrastructure.db.audit import log_audit
from purecast.infrastructure.db.models import User
from purecast.infrastructure.db.repository import BaseRepository

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_roles(Role.TENANT_ADMIN, Role.PLATFORM_ADMIN))],
)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(Role.TENANT_ADMIN, Role.PLATFORM_ADMIN))],
) -> UserResponse:
    """Create or invite a new user under the caller's tenant."""
    # Check email duplicate within tenant
    res = await session.execute(
        select(User).filter(User.tenant_id == current_user.tenant_id, User.email == req.email)
    )
    if res.scalars().first():
        raise ConflictError(f"User with email '{req.email}' already exists in this tenant")

    repo = BaseRepository(User, session)
    new_user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role.value,
        is_active=True,
    )
    saved_user = await repo.create(new_user, tenant_id=current_user.tenant_id)

    await log_audit(
        session=session,
        action="user:create",
        resource_type="user",
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        resource_id=str(saved_user.id),
    )
    return UserResponse.model_validate(saved_user, from_attributes=True)


@router.get("", response_model=list[UserResponse])
async def list_users(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(Role.TENANT_ADMIN, Role.PLATFORM_ADMIN))],
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> list[UserResponse]:
    """List users belonging to the caller's tenant."""
    repo = BaseRepository(User, session)
    users = await repo.list(
        tenant_id=current_user.tenant_id,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [UserResponse.model_validate(u, from_attributes=True) for u in users]


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: UUID,
    req: UserRoleUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(Role.TENANT_ADMIN, Role.PLATFORM_ADMIN))],
) -> UserResponse:
    """Change the RBAC role of a user in the caller's tenant."""
    repo = BaseRepository(User, session)
    user = await repo.get_by_id_or_404(user_id, tenant_id=current_user.tenant_id)

    user.role = req.role.value
    updated = await repo.update(user)

    await log_audit(
        session=session,
        action="user:change_role",
        resource_type="user",
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        resource_id=str(user.id),
        details={"new_role": req.role.value},
    )
    return UserResponse.model_validate(updated, from_attributes=True)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(Role.TENANT_ADMIN, Role.PLATFORM_ADMIN))],
) -> None:
    """Deactivate a user in the caller's tenant."""
    repo = BaseRepository(User, session)
    user = await repo.get_by_id_or_404(user_id, tenant_id=current_user.tenant_id)

    user.is_active = False
    await repo.update(user)

    await log_audit(
        session=session,
        action="user:deactivate",
        resource_type="user",
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        resource_id=str(user.id),
    )
