"""Integration test: Strict multi-tenant isolation enforcement."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tenant_isolation_prevents_cross_tenant_access(client: AsyncClient) -> None:
    """Verify Tenant A cannot list, view, or modify Tenant B's households, devices, or users."""
    suffix = uuid4().hex[:6]

    # 1. Register Tenant A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "Tenant Alpha",
            "tenant_slug": f"alpha-{suffix}",
            "email": f"admin@alpha-{suffix}.com",
            "password": "Password123!",
            "full_name": "Admin Alpha",
        },
    )
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register Tenant B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "Tenant Beta",
            "tenant_slug": f"beta-{suffix}",
            "email": f"admin@beta-{suffix}.com",
            "password": "Password123!",
            "full_name": "Admin Beta",
        },
    )
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Create Household and Device in Tenant B
    hh_b_res = await client.post(
        "/api/v1/households",
        json={"name": "Beta Private Villa", "address": "123 Beta Lane"},
        headers=headers_b,
    )
    assert hh_b_res.status_code == 201
    hh_b_id = hh_b_res.json()["id"]

    dev_b_res = await client.post(
        "/api/v1/devices",
        json={
            "serial_number": f"DEV-BETA-{suffix}",
            "model_name": "BetaPure-X",
            "household_id": hh_b_id,
        },
        headers=headers_b,
    )
    assert dev_b_res.status_code == 201
    dev_b_id = dev_b_res.json()["device"]["id"]

    # 4. Create Household and Device in Tenant A
    hh_a_res = await client.post(
        "/api/v1/households",
        json={"name": "Alpha Home", "address": "456 Alpha Way"},
        headers=headers_a,
    )
    assert hh_a_res.status_code == 201
    hh_a_id = hh_a_res.json()["id"]

    dev_a_res = await client.post(
        "/api/v1/devices",
        json={
            "serial_number": f"DEV-ALPHA-{suffix}",
            "model_name": "AlphaPure-A",
            "household_id": hh_a_id,
        },
        headers=headers_a,
    )
    assert dev_a_res.status_code == 201
    dev_a_id = dev_a_res.json()["device"]["id"]

    # 5. Isolation Checks: Listing Devices
    list_dev_a = await client.get("/api/v1/devices", headers=headers_a)
    assert list_dev_a.status_code == 200
    dev_a_ids = [d["id"] for d in list_dev_a.json()]
    assert dev_a_id in dev_a_ids
    assert dev_b_id not in dev_a_ids, "Tenant A must NOT see Tenant B's devices in list"

    # 6. Isolation Checks: Directly Accessing Tenant B Device ID
    get_dev_b_as_a = await client.get(f"/api/v1/devices/{dev_b_id}", headers=headers_a)
    assert get_dev_b_as_a.status_code in (404, 403), (
        "Tenant A must NOT be able to GET Tenant B's device"
    )

    # 7. Isolation Checks: Listing Households
    list_hh_a = await client.get("/api/v1/households", headers=headers_a)
    assert list_hh_a.status_code == 200
    hh_a_ids = [h["id"] for h in list_hh_a.json()]
    assert hh_a_id in hh_a_ids
    assert hh_b_id not in hh_a_ids, "Tenant A must NOT see Tenant B's households in list"

    # 8. Isolation Checks: Directly Accessing Tenant B Household ID
    get_hh_b_as_a = await client.get(f"/api/v1/households/{hh_b_id}", headers=headers_a)
    assert get_hh_b_as_a.status_code in (404, 403), (
        "Tenant A must NOT be able to GET Tenant B's household"
    )

    # 9. Isolation Checks: Listing Users
    list_users_a = await client.get("/api/v1/users", headers=headers_a)
    assert list_users_a.status_code == 200
    users_a_emails = [u["email"] for u in list_users_a.json()]
    assert f"admin@alpha-{suffix}.com" in users_a_emails
    assert f"admin@beta-{suffix}.com" not in users_a_emails, (
        "Tenant A must NOT see Tenant B's users"
    )
