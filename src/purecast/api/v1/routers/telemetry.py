"""Telemetry API endpoints.
Provides HTTP equivalents of the MQTT ingestion pipeline.
"""

import json
from datetime import datetime, UTC
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from purecast.api.schemas import telemetry as telemetry_schemas
from purecast.core.deps import get_current_user, get_db
from purecast.core.errors import BadRequestError
from purecast.infrastructure.db import async_session_factory, get_redis
from purecast.infrastructure.db.models import (
    Device,
    DeviceCredential,
    TelemetryReading,
    DeadLetterMessage,
)
from purecast.infrastructure.mqtt.payload_validators import (
    TelemetryPayload,
    verify_payload_hmac,
    is_timestamp_valid,
)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

async def _store_telemetry(
    session: AsyncSession,
    redis,
    tenant_id: str,
    device_id: str,
    payload: TelemetryPayload,
) -> None:
    # Reuse logic from ingestor (slightly trimmed for brevity)
    result = await session.execute(
        select(Device).where(Device.id == device_id, Device.tenant_id == tenant_id)
    )
    device: Device | None = result.scalars().first()
    if not device:
        raise BadRequestError("Device not found for tenant")
    cred: DeviceCredential | None = device.credentials
    if payload.sig and cred and cred.secret_key:
        if not verify_payload_hmac(payload.model_dump(), cred.secret_key, payload.sig):
            raise BadRequestError("Invalid HMAC signature")
    for item in payload.get_items():
        if not is_timestamp_valid(item.ts):
            raise BadRequestError("Timestamp out of range")
        replay_key = f"device:{device_id}:seq:{item.seq}"
        existed = await redis.set(replay_key, 1, ex=86400, nx=True)
        if not existed:
            raise BadRequestError("Duplicate sequence number")
        reading = TelemetryReading(
            time=datetime.fromtimestamp(item.ts, tz=UTC),
            device_id=device.id,
            tenant_id=device.tenant_id,
            pump_status=item.pump,
            pressure_p1=item.p1,
            pressure_p2=item.p2,
            pressure_p3=item.p3,
            flow_rate=item.flow_permeate,
            tds_in=item.tds_in,
            tds_out=item.tds_out,
            temperature=item.temp,
            turbidity=item.ntu,
            uv_current=item.uv_current,
        )
        session.add(reading)
    await session.commit()

@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def post_telemetry_batch(
    payload: telemetry_schemas.TelemetryBatch,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Accept a batch of telemetry items over HTTP.
    The payload mirrors the MQTT structure and is validated via the same Pydantic models.
    """
    # The request contains tenant_id derived from the authenticated user
    tenant_id = str(user.tenant_id)
    # Convert incoming DTO to internal Pydantic model used by MQTT pipeline
    telemetry_payload = TelemetryPayload(**payload.dict())
    redis = await get_redis()
    await _store_telemetry(session, redis, tenant_id, str(payload.device_id), telemetry_payload)

@router.get("/device/{device_id}", response_model=List[telemetry_schemas.TelemetryItem])
async def get_device_telemetry(
    device_id: str,
    limit: int = 100,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[telemetry_schemas.TelemetryItem]:
    """Retrieve recent telemetry readings for a device.
    Simple implementation returning the most recent rows.
    """
    result = await session.execute(
        select(TelemetryReading)
        .where(TelemetryReading.device_id == device_id, TelemetryReading.tenant_id == str(user.tenant_id))
        .order_by(TelemetryReading.time.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        telemetry_schemas.TelemetryItem(
            ts=int(row.time.timestamp()),
            seq=0,  # sequence not stored in DB; placeholder
            pump=row.pump_status,
            mode="RO",  # mode not persisted; default placeholder
            p1=row.pressure_p1,
            p2=row.pressure_p2,
            p3=row.pressure_p3,
            flow_drain=None,
            flow=row.flow_rate,
            tds_in=row.tds_in,
            tds_out=row.tds_out,
            temp=row.temperature,
            ntu=row.turbidity,
            uv_current=row.uv_current,
            litres_delta=None,
        )
        for row in rows
    ]

