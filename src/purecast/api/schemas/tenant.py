"""Tenant management schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from purecast.domain.enums import Role


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    tier: str = Field(default="FULL")


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None
    tier: str | None = None


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool
    tier: str
    created_at: datetime
    updated_at: datetime


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    role: Role = Role.DEVICE
    expires_in_days: int | None = None


class ApiKeyCreatedResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    prefix: str
    api_key: str
    role: str
    is_active: bool
    created_at: datetime


class ApiKeyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    prefix: str
    role: str
    is_active: bool
    created_at: datetime

