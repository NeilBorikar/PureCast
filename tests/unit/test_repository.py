"""Unit tests for generic repository and tenant isolation enforcement."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.core.errors import TenantMismatchError
from purecast.core.security import hash_password
from purecast.domain.enums import Role
from purecast.infrastructure.db.models import Tenant, User
from purecast.infrastructure.db.repository import BaseRepository


@pytest.mark.asyncio
async def test_repository_requires_tenant_id_for_scoped_entities(db_session: AsyncSession) -> None:
    """Ensure BaseRepository raises TenantMismatchError when tenant_id is None."""
    repo = BaseRepository(User, db_session)

    with pytest.raises(TenantMismatchError, match="Tenant context required"):
        await repo.list(tenant_id=None)

    with pytest.raises(TenantMismatchError, match="Tenant context required"):
        await repo.get_by_id(entity_id=uuid4(), tenant_id=None)


@pytest.mark.asyncio
async def test_repository_crud_flow_with_tenant(db_session: AsyncSession) -> None:
    """Validate full CRUD lifecycle using BaseRepository with tenant scoping."""
    # Create tenant
    tenant_repo = BaseRepository(Tenant, db_session)
    tenant = Tenant(name="Test Tenant", slug=f"test-{uuid4().hex[:8]}", tier="FULL")
    saved_tenant = await tenant_repo.create(tenant)

    # Create user in tenant
    user_repo = BaseRepository(User, db_session)
    user = User(
        email=f"user-{uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Test User",
        role=Role.TENANT_ADMIN.value,
        is_active=True,
    )
    saved_user = await user_repo.create(user, tenant_id=saved_tenant.id)
    assert saved_user.tenant_id == saved_tenant.id

    # Retrieve by id with correct tenant
    found = await user_repo.get_by_id(saved_user.id, tenant_id=saved_tenant.id)
    assert found is not None
    assert found.email == saved_user.email

    # Retrieve by id with foreign tenant returns None
    other_tenant_id = uuid4()
    foreign = await user_repo.get_by_id(saved_user.id, tenant_id=other_tenant_id)
    assert foreign is None

    # Delete
    deleted = await user_repo.delete_by_id(saved_user.id, tenant_id=saved_tenant.id)
    assert deleted is True

    # Confirm deletion
    assert await user_repo.get_by_id(saved_user.id, tenant_id=saved_tenant.id) is None
