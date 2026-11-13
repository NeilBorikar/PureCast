"""Device management schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from purecast.domain.enums import DeviceTier, OperatingMode


class DeviceCreate(BaseModel):
    serial_number: str = Field(..., min_length=2, max_length=100)
    device_tier: DeviceTier = DeviceTier.FULL
    model_name: str = Field(..., min_length=2, max_length=100)
    operating_mode: OperatingMode = OperatingMode.RO
    household_id: UUID | None = None


class DeviceUpdate(BaseModel):
    model_name: str | None = None
    operating_mode: OperatingMode | None = None
    household_id: UUID | None = None
    is_active: bool | None = None


class DeviceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    household_id: UUID | None
    serial_number: str
    device_tier: str
    model_name: str
    operating_mode: str
    is_active: bool
    installed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DeviceCredentialsResponse(BaseModel):
    device: DeviceResponse
    client_id: str
    secret: str

