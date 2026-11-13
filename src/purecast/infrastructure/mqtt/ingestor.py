'''Ingestor for MQTT telemetry using aiomqtt.
Implements subscription to telemetry, status, and events topics.
Validates payloads via `payload_validators` and stores telemetry
readings into the database. Invalid messages are persisted to the
`DeadLetterMessage` table for later inspection.
''' 

import asyncio
from datetime import datetime, UTC
import json
import logging
from typing import Any

import aiomqtt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from purecast.core.config import Settings
from purecast.infrastructure.db import async_session_factory, get_redis
from purecast.infrastructure.db.models import (
    Device,
    DeviceCredential,
    TelemetryReading,
    DeadLetterMessage,
)
from purecast.infrastructure.mqtt.payload_validators import (
    TelemetryPayload,
    StatusPayload,
    EventPayload,
    verify_payload_hmac,
    is_timestamp_valid,
)

logger = logging.getLogger(__name__)


async def _process_telemetry(
    session: AsyncSession, redis, tenant_id: str, device_id: str, payload: TelemetryPayload
) -> None:
    """Validate and store telemetry items.

    * HMAC verification (if secret configured)
    * Timestamp and replay protection via Redis
    * Batch insertion of ``TelemetryReading`` rows
    """
    # Load device and credential
    result = await session.execute(
        select(Device).where(Device.id == device_id, Device.tenant_id == tenant_id)
    )
    device: Device | None = result.scalars().first()
    if not device:
        raise ValueError(f"Device {device_id} not found for tenant {tenant_id}")

    cred: DeviceCredential | None = device.credentials  # type: ignore[assignment]
    if payload.sig and cred and cred.secret_key:
        if not verify_payload_hmac(payload.model_dump(), cred.secret_key, payload.sig):
            raise ValueError("Invalid HMAC signature")

    for item in payload.get_items():
        # timestamp validation
        if not is_timestamp_valid(item.ts):
            raise ValueError("Timestamp out of allowed range")
        # replay protection – unique seq per device
        replay_key = f"device:{device_id}:seq:{item.seq}"
        existed = await redis.set(replay_key, 1, ex=86400, nx=True)  # 1‑day TTL
        if not existed:
            raise ValueError("Duplicate sequence number detected")

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
            # litres_delta is not stored directly – derived elsewhere
        )
        session.add(reading)
    await session.commit()


async def _process_status(session: AsyncSession, tenant_id: str, device_id: str, payload: StatusPayload) -> None:
    result = await session.execute(
        select(Device).where(Device.id == device_id, Device.tenant_id == tenant_id)
    )
    device: Device | None = result.scalars().first()
    if not device:
        raise ValueError(f"Device {device_id} not found for tenant {tenant_id}")
    device.online_status = payload.status.upper()
    device.last_seen_at = datetime.now(UTC)
    await session.commit()


async def _process_event(session: AsyncSession, tenant_id: str, device_id: str, payload: EventPayload) -> None:
    # For now we just store the event as a generic ``Event`` model – omitted for brevity
    # Placeholder to satisfy the contract.
    logger.info("Received event %s from %s", payload.event_type, device_id)


async def _handle_message(
    session: AsyncSession, redis, topic: str, payload_bytes: bytes
) -> None:
    # Topic format: purecast/{tenant_id}/{device_id}/{type}
    parts = topic.split('/')
    if len(parts) != 4:
        raise ValueError(f"Malformed topic {topic}")
    _, tenant_id, device_id, msg_type = parts
    data = json.loads(payload_bytes)
    if msg_type == "telemetry":
        pl = TelemetryPayload.model_validate(data)
        await _process_telemetry(session, redis, tenant_id, device_id, pl)
    elif msg_type == "status":
        pl = StatusPayload.model_validate(data)
        await _process_status(session, tenant_id, device_id, pl)
    elif msg_type == "events":
        pl = EventPayload.model_validate(data)
        await _process_event(session, tenant_id, device_id, pl)
    else:
        raise ValueError(f"Unsupported message type {msg_type}")


async def _ingest_loop() -> None:
    settings = Settings()
    redis = await get_redis()
    async with async_session_factory() as session:
        async with aiomqtt.Client(
            hostname=settings.mqtt_host,
            port=settings.mqtt_port,
            username=settings.mqtt_user,
            password=settings.mqtt_password,
        ) as client:
            # Subscribe to all three topics using wildcards
            await client.subscribe("purecast/+/+/telemetry")
            await client.subscribe("purecast/+/+/status")
            await client.subscribe("purecast/+/+/events")
            logger.info("MQTT ingestor subscribed to telemetry, status, events")
            async for message in client.messages:
                try:
                    await _handle_message(session, redis, message.topic.value, message.payload)
                except Exception as exc:  # pragma: no cover – defensive
                    # Persist dead‑letter for later analysis
                    dl = DeadLetterMessage(
                        tenant_id=message.topic.value.split('/')[1],
                        device_id=message.topic.value.split('/')[2],
                        topic=message.topic.value,
                        payload=message.payload.decode(errors="ignore"),
                        error=str(exc),
                    )
                    session.add(dl)
                    await session.commit()
                    logger.exception("Failed to process MQTT message %s", message.topic.value)


def main() -> None:
    asyncio.run(_ingest_loop())


if __name__ == "__main__":
    main()
