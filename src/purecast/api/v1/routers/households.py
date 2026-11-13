"""Household CRUD endpoints enforcing tenant isolation."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.api.schemas.household import (
    HouseholdCreate,
    HouseholdResponse,
    HouseholdUpdate,
)
from purecast.core.deps import (
    PaginationParams,
    get_current_user,
    get_db,
    get_pagination,
    require_roles,
)
from purecast.domain.enums import Role
from purecast.infrastructure.db.audit import log_audit
from purecast.infrastructure.db.models import Household, User
from purecast.infrastructure.db.repository import BaseRepository

router = APIRouter(
    prefix="/households",
    tags=["households"],
    dependencies=[
        Depends(
            require_roles(
                Role.PLATFORM_ADMIN,
                Role.TENANT_ADMIN,
                Role.TENANT_ANALYST,
                Role.HOUSEHOLD_OWNER,
            )
        )
    ],
)


@router.post("", response_model=HouseholdResponse, status_code=status.HTTP_201_CREATED)
async def create_household(
    req: HouseholdCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> HouseholdResponse:
    """Create a new household record within caller's tenant."""
    repo = BaseRepository(Household, session)
    household = Household(
        name=req.name,
        address=req.address,
        owner_user_id=req.owner_user_id or current_user.id,
    )
    saved = await repo.create(household, tenant_id=current_user.tenant_id)

    await log_audit(
        session=session,
        action="household:create",
        resource_type="household",
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        resource_id=str(saved.id),
    )
    return HouseholdResponse.model_validate(saved, from_attributes=True)


@router.get("", response_model=list[HouseholdResponse])
async def list_households(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> list[HouseholdResponse]:
    """List households belonging to caller's tenant."""
    repo = BaseRepository(Household, session)
    households = await repo.list(
        tenant_id=current_user.tenant_id,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [HouseholdResponse.model_validate(h, from_attributes=True) for h in households]


@router.get("/{household_id}", response_model=HouseholdResponse)
async def get_household(
    household_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> HouseholdResponse:
    """Get single household within caller's tenant."""
    repo = BaseRepository(Household, session)
    household = await repo.get_by_id_or_404(household_id, tenant_id=current_user.tenant_id)
    return HouseholdResponse.model_validate(household, from_attributes=True)


@router.patch("/{household_id}", response_model=HouseholdResponse)
async def update_household(
    household_id: UUID,
    req: HouseholdUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> HouseholdResponse:
    """Update household details within caller's tenant."""
    repo = BaseRepository(Household, session)
    household = await repo.get_by_id_or_404(household_id, tenant_id=current_user.tenant_id)

    if req.name is not None:
        household.name = req.name
    if req.address is not None:
        household.address = req.address
    if req.owner_user_id is not None:
        household.owner_user_id = req.owner_user_id

    updated = await repo.update(household)
    await log_audit(
        session=session,
        action="household:update",
        resource_type="household",
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        resource_id=str(updated.id),
    )
    return HouseholdResponse.model_validate(updated, from_attributes=True)


@router.delete("/{household_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_household(
    household_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a household from caller's tenant."""
    repo = BaseRepository(Household, session)
    await repo.get_by_id_or_404(household_id, tenant_id=current_user.tenant_id)
    await repo.delete_by_id(household_id, tenant_id=current_user.tenant_id)

    await log_audit(
        session=session,
        action="household:delete",
        resource_type="household",
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        resource_id=str(household_id),
    )

