"""Audit log helper for security, auth, and tenant-critical actions."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from purecast.infrastructure.db.models import AuditLog


async def log_audit(
    session: AsyncSession,
    action: str,
    resource_type: str,
    tenant_id: UUID | None = None,
    user_id: UUID | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record an immutable audit log entry."""
    entry = AuditLog(
        action=action,
        resource_type=resource_type,
        tenant_id=tenant_id,
        user_id=user_id,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
    )
    session.add(entry)
    await session.flush()
    return entry
