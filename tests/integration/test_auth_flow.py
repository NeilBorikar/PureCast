"""Integration test: Full authentication and token rotation lifecycle."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_auth_and_rotation_lifecycle(client: AsyncClient) -> None:
    """Test register -> login -> me -> refresh rotation -> logout flow."""
    rand_suffix = uuid4().hex[:6]
    tenant_slug = f"acme-{rand_suffix}"
    email = f"admin@{tenant_slug}.com"
    password = "StrongPassword2026!"

    # 1. Register
    reg_payload = {
        "tenant_name": "ACME Water Solutions",
        "tenant_slug": tenant_slug,
        "email": email,
        "password": password,
        "full_name": "ACME Administrator",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    access_token = reg_data["access_token"]
    assert reg_data["refresh_token"] is not None

    # 2. Get Me (using access token)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200, me_res.text
    me_data = me_res.json()
    assert me_data["email"] == email
    assert me_data["role"] == "TENANT_ADMIN"

    # 3. Login
    login_payload = {"email": email, "password": password}
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200, login_res.text
    login_data = login_res.json()
    assert login_data["access_token"] is not None
    new_refresh = login_data["refresh_token"]

    # 4. Refresh token rotation
    ref_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert ref_res.status_code == 200, ref_res.text
    ref_data = ref_res.json()
    assert ref_data["access_token"] is not None
    rotated_refresh = ref_data["refresh_token"]
    assert rotated_refresh != new_refresh

    # 5. Token reuse detection: attempting to reuse old refresh token must be rejected
    reuse_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert reuse_res.status_code == 401, "Expected 401 on consumed refresh token reuse"

    # 6. Logout using the rotated refresh token
    logout_res = await client.post("/api/v1/auth/logout", json={"refresh_token": rotated_refresh})
    assert logout_res.status_code == 204

    # 7. Post-logout refresh must fail
    post_logout_res = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": rotated_refresh}
    )
    assert post_logout_res.status_code == 401
