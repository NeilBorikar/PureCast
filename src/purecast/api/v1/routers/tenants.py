"""Platform administration: Tenant lifecycle and API key management."""

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.api.schemas.tenant import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)
from purecast.core.deps import PaginationParams, get_db, get_pagination, require_roles
from purecast.core.errors import ConflictError, NotFoundError
from purecast.core.security import generate_api_key
from purecast.domain.enums import Role
from purecast.infrastructure.db.audit import log_audit
from purecast.infrastructure.db.models import ApiKey, Tenant, User

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    dependencies=[Depends(require_roles(Role.PLATFORM_ADMIN))],
)


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    req: TenantCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(Role.PLATFORM_ADMIN))],
) -> TenantResponse:
    """Create a new tenant organization (Platform Admin only)."""
    res = await session.execute(select(Tenant).filter(Tenant.slug == req.slug))
    if res.scalars().first():
        raise ConflictError(f"Tenant slug '{req.slug}' is already taken")

    tenant = Tenant(name=req.name, slug=req.slug, tier=req.tier, is_active=True)
    session.add(tenant)
    await session.flush()
    await session.refresh(tenant)

    await log_audit(
        session=session,
        action="tenant:create",
        resource_type="tenant",
        tenant_id=tenant.id,
        user_id=current_user.id,
        resource_id=str(tenant.id),
    )
    return TenantResponse.model_validate(tenant, from_attributes=True)


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    session: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> list[TenantResponse]:
    """List all tenants with pagination (Platform Admin only)."""
    res = await session.execute(select(Tenant).offset(pagination.skip).limit(pagination.limit))
    tenants = res.scalars().all()
    return [TenantResponse.model_validate(t, from_attributes=True) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TenantResponse:
    """Fetch tenant details by ID (Platform Admin only)."""
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise NotFoundError("Tenant not found")
    return TenantResponse.model_validate(tenant, from_attributes=True)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    req: TenantUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(Role.PLATFORM_ADMIN))],
) -> TenantResponse:
    """Update tenant configuration (Platform Admin only)."""
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise NotFoundError("Tenant not found")

    if req.name is not None:
        tenant.name = req.name
    if req.is_active is not None:
        tenant.is_active = req.is_active
    if req.tier is not None:
        tenant.tier = req.tier

    session.add(tenant)
    await session.flush()
    await session.refresh(tenant)

    await log_audit(
        session=session,
        action="tenant:update",
        resource_type="tenant",
        tenant_id=tenant.id,
        user_id=current_user.id,
        resource_id=str(tenant.id),
    )
    return TenantResponse.model_validate(tenant, from_attributes=True)


@router.post(
    "/{tenant_id}/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    tenant_id: UUID,
    req: ApiKeyCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(Role.PLATFORM_ADMIN))],
) -> ApiKeyCreatedResponse:
    """Issue a new API key for the tenant (shown once only)."""
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise NotFoundError("Tenant not found")

    raw_key, key_hash, prefix = generate_api_key()
    expires_at = (
        datetime.now(UTC) + timedelta(days=req.expires_in_days) if req.expires_in_days else None
    )

    api_key_obj = ApiKey(
        tenant_id=tenant_id,
        name=req.name,
        key_hash=key_hash,
        prefix=prefix,
        role=req.role.value,
        is_active=True,
        expires_at=expires_at,
    )
    session.add(api_key_obj)
    await session.flush()
    await session.refresh(api_key_obj)

    await log_audit(
        session=session,
        action="api_key:create",
        resource_type="api_key",
        tenant_id=tenant_id,
        user_id=current_user.id,
        resource_id=str(api_key_obj.id),
    )

    return ApiKeyCreatedResponse(
        id=api_key_obj.id,
        tenant_id=api_key_obj.tenant_id,
        name=api_key_obj.name,
        prefix=api_key_obj.prefix,
        api_key=raw_key,
        role=api_key_obj.role,
        is_active=api_key_obj.is_active,
        created_at=api_key_obj.created_at,
    )


@router.get("/{tenant_id}/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    tenant_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ApiKeyResponse]:
    """List all API keys belonging to a tenant."""
    res = await session.execute(select(ApiKey).filter(ApiKey.tenant_id == tenant_id))
    keys = res.scalars().all()
    return [ApiKeyResponse.model_validate(k, from_attributes=True) for k in keys]


@router.delete("/{tenant_id}/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    tenant_id: UUID,
    key_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(Role.PLATFORM_ADMIN))],
) -> None:
    """Revoke or delete a tenant API key."""
    res = await session.execute(
        select(ApiKey).filter(ApiKey.id == key_id, ApiKey.tenant_id == tenant_id)
    )
    key_obj = res.scalars().first()
    if not key_obj:
        raise NotFoundError("API Key not found")

    await session.delete(key_obj)
    await session.flush()

    await log_audit(
        session=session,
        action="api_key:revoke",
        resource_type="api_key",
        tenant_id=tenant_id,
        user_id=current_user.id,
        resource_id=str(key_id),
    )
