"""Device management and credential provisioning endpoints."""

import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.api.schemas.device import (
    DeviceCreate,
    DeviceCredentialsResponse,
    DeviceResponse,
    DeviceUpdate,
)
from purecast.core.deps import (
    PaginationParams,
    get_current_user,
    get_db,
    get_pagination,
    require_roles,
)
from purecast.core.errors import ConflictError
from purecast.core.security import hash_password
from purecast.domain.enums import Role
from purecast.infrastructure.db.audit import log_audit
from purecast.infrastructure.db.models import Device, DeviceCredential, User
from purecast.infrastructure.db.repository import BaseRepository

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    dependencies=[
        Depends(
            require_roles(
                Role.PLATFORM_ADMIN,
                Role.TENANT_ADMIN,
                Role.TENANT_ANALYST,
                Role.SERVICE_TECHNICIAN,
                Role.HOUSEHOLD_OWNER,
            )
        )
    ],
)


@router.post("", response_model=DeviceCredentialsResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    req: DeviceCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DeviceCredentialsResponse:
    """Register a new device and return connection credentials ONCE."""
    # Check duplicate serial number
    res = await session.execute(select(Device).filter(Device.serial_number == req.serial_number))
    if res.scalars().first():
        raise ConflictError(f"Device with serial number '{req.serial_number}' already registered")

    repo = BaseRepository(Device, session)
    device = Device(
        serial_number=req.serial_number,
        device_tier=req.device_tier.value,
        model_name=req.model_name,
        operating_mode=req.operating_mode.value,
        household_id=req.household_id,
        is_active=True,
    )
    saved = await repo.create(device, tenant_id=current_user.tenant_id)

    # Generate edge credentials
    client_id = f"purecast_{saved.serial_number}"
    raw_secret = secrets.token_urlsafe(32)
    credential = DeviceCredential(
        tenant_id=current_user.tenant_id,
        device_id=saved.id,
        client_id=client_id,
        hashed_secret=hash_password(raw_secret),
        secret_key=raw_secret,
    )
    session.add(credential)
    await session.flush()

    await log_audit(
        session=session,
        action="device:create",
        resource_type="device",
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        resource_id=str(saved.id),
    )

    return DeviceCredentialsResponse(
        device=DeviceResponse.model_validate(saved, from_attributes=True),
        client_id=client_id,
        secret=raw_secret,
    )


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> list[DeviceResponse]:
    """List devices in caller's tenant."""
    repo = BaseRepository(Device, session)
    devices = await repo.list(
        tenant_id=current_user.tenant_id,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [DeviceResponse.model_validate(d, from_attributes=True) for d in devices]


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DeviceResponse:
    """Fetch single device in caller's tenant."""
    repo = BaseRepository(Device, session)
    device = await repo.get_by_id_or_404(device_id, tenant_id=current_user.tenant_id)
    return DeviceResponse.model_validate(device, from_attributes=True)


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    req: DeviceUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DeviceResponse:
    """Update device metadata in caller's tenant."""
    repo = BaseRepository(Device, session)
    device = await repo.get_by_id_or_404(device_id, tenant_id=current_user.tenant_id)

    if req.model_name is not None:
        device.model_name = req.model_name
    if req.operating_mode is not None:
        device.operating_mode = req.operating_mode.value
    if req.household_id is not None:
        device.household_id = req.household_id
    if req.is_active is not None:
        device.is_active = req.is_active

    updated = await repo.update(device)
    await log_audit(
        session=session,
        action="device:update",
        resource_type="device",
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        resource_id=str(updated.id),
    )
    return DeviceResponse.model_validate(updated, from_attributes=True)

