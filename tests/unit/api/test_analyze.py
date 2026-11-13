"""Unit and integration test for POST /api/v1/analyze endpoint."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.core.security import create_access_token, hash_password
from purecast.domain.enums import ConsumableType, Role
from purecast.infrastructure.db.models import Tenant, User


@pytest.mark.asyncio
async def test_analyze_endpoint_authenticated(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """POST /api/v1/analyze accepts readings + optional device_state and returns AnalysisResult."""
    suffix = uuid4().hex[:6]
    tenant = Tenant(
        name=f"Analyze Test Tenant {suffix}",
        slug=f"tenant-analyze-{suffix}",
        tier="ENTERPRISE",
        is_active=True,
    )
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email=f"technician-{suffix}@purecast.io",
        hashed_password=hash_password("TechPass2026!"),
        full_name="Field Technician",
        role=Role.SERVICE_TECHNICIAN.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=Role.SERVICE_TECHNICIAN.value,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test unauthenticated request is rejected
    unauth_res = await client.post(
        "/api/v1/analyze",
        json={"readings": []},
    )
    assert unauth_res.status_code in (401, 403)

    # 2. Test authenticated request with valid readings
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "readings": [
            {
                "timestamp": now,
                "pump_running": True,
                "pressure_p1": 50.0,
                "pressure_p2": 45.0,
                "pressure_p3": 45.0,
                "flow_rate": 1.20,
                "tds_in": 500.0,
                "tds_out": 10.0,
                "temperature": 25.0,
                "turbidity": 0.5,
                "uv_current": 400.0,
                "operating_mode": "RO",
                "device_tier": "FULL",
            }
        ],
        "device_state": None,
    }

    res = await client.post("/api/v1/analyze", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    # Validate schema
    assert "stages" in data
    assert "active_diagnoses" in data
    assert "event_tags" in data
    assert "is_lite_mode" in data
    assert "updated_device_state" in data

    # Validate all 5 stages exist
    stages = data["stages"]
    for stg in (
        ConsumableType.SEDIMENT.value,
        ConsumableType.CARBON.value,
        ConsumableType.MEMBRANE_PROTECTOR.value,
        ConsumableType.RO_MEMBRANE.value,
        ConsumableType.UV_LAMP.value,
    ):
        assert stg in stages
        assert "health_percent" in stages[stg]
        assert "status_text" in stages[stg]
        assert 0.0 <= stages[stg]["health_percent"] <= 100.0

    # 3. Test subsequent call passing updated_device_state
    next_payload = {
        "readings": payload["readings"],
        "device_state": data["updated_device_state"],
    }
    next_res = await client.post("/api/v1/analyze", json=next_payload, headers=headers)
    assert next_res.status_code == 200
    next_data = next_res.json()
    assert next_data["updated_device_state"]["baseline"]["is_established"] is not None

