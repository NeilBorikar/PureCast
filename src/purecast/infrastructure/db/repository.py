"""Generic repository enforcing strict multi-tenant isolation."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.core.errors import NotFoundError, TenantMismatchError
from purecast.infrastructure.db.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):  # noqa: UP046
    """Generic repository enforcing tenant_id filtering on all queries."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session
        self._is_tenant_scoped = hasattr(model, "tenant_id")

    def _apply_tenant_filter(self, query: Any, tenant_id: UUID | None) -> Any:
        if self._is_tenant_scoped:
            if tenant_id is None:
                raise TenantMismatchError("Tenant context required for tenant-scoped resource")
            query = query.filter(self.model.tenant_id == tenant_id)
        return query

    async def get_by_id(
        self,
        entity_id: UUID | None = None,
        tenant_id: UUID | None = None,
        id: UUID | None = None,  # noqa: A002
    ) -> ModelType | None:
        """Fetch a single record by primary key, verifying tenant isolation."""
        target_id = entity_id or id
        query = select(self.model).filter(self.model.id == target_id)
        query = self._apply_tenant_filter(query, tenant_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_id_or_404(self, entity_id: UUID, tenant_id: UUID | None = None) -> ModelType:
        """Fetch a record by primary key or raise NotFoundError."""
        obj = await self.get_by_id(entity_id, tenant_id)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} not found")
        return obj

    async def list(
        self,
        tenant_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        """List records with pagination and mandatory tenant scoping."""
        query = select(self.model)
        query = self._apply_tenant_filter(query, tenant_id)

        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, instance: ModelType, tenant_id: UUID | None = None) -> ModelType:
        """Persist a new record, setting tenant_id if tenant-scoped."""
        if self._is_tenant_scoped:
            if tenant_id is not None:
                instance.tenant_id = tenant_id
            elif getattr(instance, "tenant_id", None) is None:
                raise TenantMismatchError("Cannot create tenant-scoped resource without tenant_id")

        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """Save updates to an existing attached instance."""
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete_by_id(self, entity_id: UUID, tenant_id: UUID | None = None) -> bool:
        """Delete a record by primary key with tenant isolation check."""
        obj = await self.get_by_id(entity_id, tenant_id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        return True
