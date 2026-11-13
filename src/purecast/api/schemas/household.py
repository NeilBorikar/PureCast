"""Household management schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HouseholdCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    address: str | None = None
    owner_user_id: UUID | None = None


class HouseholdUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    address: str | None = None
    owner_user_id: UUID | None = None


class HouseholdResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    address: str | None
    owner_user_id: UUID | None
    created_at: datetime
    updated_at: datetime

