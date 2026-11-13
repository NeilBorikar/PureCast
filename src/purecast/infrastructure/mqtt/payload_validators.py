"""Pydantic v2 models and cryptographic validators for MQTT payloads."""

import hashlib
import hmac
import json
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from purecast.domain.enums import OperatingMode


def canonical_json_bytes(data: dict[str, Any]) -> bytes:
    """Serialize dictionary canonically for deterministic HMAC signature verification."""
    clean = {k: v for k, v in data.items() if k != "sig"}
    return json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_payload_hmac(data: dict[str, Any], secret: str) -> str:
    """Compute hex-encoded HMAC-SHA256 signature over payload bytes."""
    raw_bytes = canonical_json_bytes(data)
    return hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()


def verify_payload_hmac(data: dict[str, Any], secret: str, sig: str) -> bool:
    """Verify incoming signature against computed HMAC-SHA256."""
    expected = compute_payload_hmac(data, secret)
    return hmac.compare_digest(expected.lower(), sig.lower())


def is_timestamp_valid(ts: int, max_future_skew_sec: int = 600) -> bool:
    """Reject timestamp if more than 10 minutes in the future."""
    now = int(time.time())
    return ts <= (now + max_future_skew_sec)


class TelemetryItem(BaseModel):
    """Individual sensor telemetry observation."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    ts: int = Field(..., description="Epoch seconds timestamp")
    seq: int = Field(..., description="Monotonically increasing sequence number")
    pump: bool = Field(..., description="Booster pump energized state")
    mode: OperatingMode = Field(default=OperatingMode.RO, description="Operating mode")

    p1: float | None = Field(default=None, description="Pre-filter inlet pressure (psi)")
    p2: float | None = Field(default=None, description="Pre-filter outlet pressure (psi)")
    p3: float | None = Field(default=None, description="RO membrane feed pressure (psi)")

    flow_drain: float | None = Field(default=None, description="Drain concentrate flow (L/min)")
    flow_permeate: float | None = Field(
        default=None, alias="flow", description="Permeate flow rate (L/min)"
    )

    tds_in: float | None = Field(default=None, alias="tin", description="Inlet TDS (ppm)")
    tds_out: float | None = Field(default=None, alias="tout", description="Permeate TDS (ppm)")

    temp: float | None = Field(default=None, alias="temperature", description="Temperature (°C)")
    ntu: float | None = Field(default=None, alias="turb", description="Turbidity (NTU)")
    uv_current: float | None = Field(default=None, alias="uv_i", description="UV current (mA)")
    litres_delta: float | None = Field(default=None, description="Volume delta produced (L)")


class TelemetryPayload(BaseModel):
    """Incoming MQTT telemetry packet (either single sample or batch list)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    v: int = Field(default=1, description="Protocol schema version")
    sig: str | None = Field(default=None, description="HMAC-SHA256 signature")

    # Either batch is populated or single item fields are populated
    batch: list[TelemetryItem] | None = Field(default=None, description="List of backfill samples")

    # Single item fields
    ts: int | None = None
    seq: int | None = None
    pump: bool | None = None
    mode: OperatingMode = OperatingMode.RO
    p1: float | None = None
    p2: float | None = None
    p3: float | None = None
    flow_drain: float | None = None
    flow_permeate: float | None = Field(default=None, alias="flow")
    tds_in: float | None = Field(default=None, alias="tin")
    tds_out: float | None = Field(default=None, alias="tout")
    temp: float | None = Field(default=None, alias="temperature")
    ntu: float | None = Field(default=None, alias="turb")
    uv_current: float | None = Field(default=None, alias="uv_i")
    litres_delta: float | None = None

    @model_validator(mode="after")
    def validate_content(self) -> "TelemetryPayload":
        if self.batch is not None and len(self.batch) > 0:
            return self
        if self.ts is None or self.seq is None or self.pump is None:
            raise ValueError("Payload must contain either a non-empty 'batch' or 'ts', 'seq', 'pump'")
        return self

    def get_items(self) -> list[TelemetryItem]:
        """Normalize into a list of TelemetryItem records."""
        if self.batch is not None:
            return self.batch
        return [
            TelemetryItem(
                ts=self.ts,  # type: ignore[arg-type]
                seq=self.seq,  # type: ignore[arg-type]
                pump=self.pump,  # type: ignore[arg-type]
                mode=self.mode,
                p1=self.p1,
                p2=self.p2,
                p3=self.p3,
                flow_drain=self.flow_drain,
                flow_permeate=self.flow_permeate,
                tds_in=self.tds_in,
                tds_out=self.tds_out,
                temp=self.temp,
                ntu=self.ntu,
                uv_current=self.uv_current,
                litres_delta=self.litres_delta,
            )
        ]


class StatusPayload(BaseModel):
    """Device status and connectivity heartbeat payload."""

    model_config = ConfigDict(extra="ignore")

    status: str = Field(..., description="Device connectivity status, e.g. ONLINE, OFFLINE")
    ts: int | None = Field(default=None, description="Timestamp")
    firmware: str | None = Field(default=None, description="Firmware version")
    ip: str | None = Field(default=None, description="Local IP address")
    rssi: float | None = Field(default=None, description="Wi-Fi RSSI dBm")


class EventPayload(BaseModel):
    """External operational event notification payload."""

    model_config = ConfigDict(extra="ignore")

    event_type: str = Field(..., description="Event type, e.g. POWER_CUT, HOLIDAY")
    ts: int | None = Field(default=None, description="Timestamp")
    description: str | None = Field(default=None, description="Human explanation")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary event metadata")

