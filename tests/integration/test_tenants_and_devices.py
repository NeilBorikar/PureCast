"""Integration test: Platform Admin, API Keys, and Health endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.core.security import create_access_token, hash_password
from purecast.domain.enums import Role
from purecast.infrastructure.db.models import Tenant, User


@pytest.mark.asyncio
async def test_platform_admin_and_api_keys(client: AsyncClient, db_session: AsyncSession) -> None:
    """Validate platform admin permissions, tenant creation, and API key provisioning."""
    suffix = uuid4().hex[:6]

    # Create root platform tenant and platform admin user in the database
    platform_tenant = Tenant(
        name="PureCast Platform Root",
        slug=f"platform-{suffix}",
        tier="ENTERPRISE",
        is_active=True,
    )
    db_session.add(platform_tenant)
    await db_session.flush()

    platform_user = User(
        tenant_id=platform_tenant.id,
        email=f"superadmin-{suffix}@purecast.io",
        hashed_password=hash_password("SuperAdminPass2026!"),
        full_name="Platform SuperAdmin",
        role=Role.PLATFORM_ADMIN.value,
        is_active=True,
    )
    db_session.add(platform_user)
    await db_session.commit()

    # Create token for platform admin
    admin_token = create_access_token(
        subject=str(platform_user.id),
        tenant_id=str(platform_tenant.id),
        role=Role.PLATFORM_ADMIN.value,
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Platform Admin creates new tenant
    tenant_res = await client.post(
        "/api/v1/tenants",
        json={"name": "Kent RO Systems", "slug": f"kent-{suffix}", "tier": "ENTERPRISE"},
        headers=admin_headers,
    )
    assert tenant_res.status_code == 201, tenant_res.text
    tenant_id = tenant_res.json()["id"]

    # 2. Platform Admin generates API key for the tenant
    key_res = await client.post(
        f"/api/v1/tenants/{tenant_id}/api-keys",
        json={"name": "Factory Ingestor Key", "role": "DEVICE", "expires_in_days": 30},
        headers=admin_headers,
    )
    assert key_res.status_code == 201, key_res.text
    key_data = key_res.json()
    assert "api_key" in key_data
    raw_api_key = key_data["api_key"]
    assert raw_api_key.startswith("pc_live_")

    # 3. List API keys
    list_keys_res = await client.get(f"/api/v1/tenants/{tenant_id}/api-keys", headers=admin_headers)
    assert list_keys_res.status_code == 200
    assert len(list_keys_res.json()) >= 1

    # 4. Create a tenant-admin user in Kent tenant
    kent_admin = User(
        tenant_id=platform_tenant.id,
        email=f"kent-admin-{suffix}@kent.com",
        hashed_password=hash_password("KentPass123!"),
        full_name="Kent Admin",
        role=Role.TENANT_ADMIN.value,
        is_active=True,
    )
    db_session.add(kent_admin)
    await db_session.commit()

    # Non-platform admin receives 403 trying to access /api/v1/tenants
    tenant_admin_token = create_access_token(
        subject=str(kent_admin.id),
        tenant_id=str(platform_tenant.id),
        role=Role.TENANT_ADMIN.value,
    )
    ta_headers = {"Authorization": f"Bearer {tenant_admin_token}"}
    forbidden_res = await client.get("/api/v1/tenants", headers=ta_headers)
    assert forbidden_res.status_code == 403


@pytest.mark.asyncio
async def test_health_and_version_endpoints(client: AsyncClient) -> None:
    """Validate health probes and version endpoint."""
    # Liveness
    live_res = await client.get("/health/live")
    assert live_res.status_code == 200
    assert live_res.json() == {"status": "alive"}

    # Readiness
    ready_res = await client.get("/health/ready")
    assert ready_res.status_code in (200, 503)

    # Version
    ver_res = await client.get("/version")
    assert ver_res.status_code == 200
    data = ver_res.json()
    assert data["service"] == "PureCast API"
    assert "version" in data
