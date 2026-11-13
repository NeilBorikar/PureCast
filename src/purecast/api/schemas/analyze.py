"""Pydantic schemas for the telemetry analysis advisory endpoint."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from purecast.domain.enums import (
    ConsumableType,
    DeviceTier,
    EventType,
    FaultType,
    OperatingMode,
    SensorFaultType,
)


class ReadingInput(BaseModel):
    """Single sensor telemetry sample."""

    timestamp: datetime = Field(..., description="Timestamp of the telemetry reading")
    pump_running: bool = Field(..., description="Whether the booster pump was energized")
    pressure_p1: float | None = Field(None, description="Pre-sediment inlet pressure (psi)")
    pressure_p2: float | None = Field(None, description="Post-carbon pressure (psi)")
    pressure_p3: float | None = Field(None, description="RO membrane feed driving pressure (psi)")
    flow_rate: float | None = Field(None, description="Permeate flow rate (L/min)")
    tds_in: float | None = Field(None, description="Inlet raw water TDS (ppm)")
    tds_out: float | None = Field(None, description="Permeate purified water TDS (ppm)")
    temperature: float | None = Field(None, description="Feed water temperature (°C)")
    turbidity: float | None = Field(None, description="Raw feed water turbidity (NTU)")
    uv_current: float | None = Field(None, description="UV disinfection lamp ballast current (mA)")
    operating_mode: OperatingMode = Field(default=OperatingMode.RO, description="Operating mode")
    device_tier: DeviceTier = Field(default=DeviceTier.FULL, description="Device tier capability")


class AnalyzeRequest(BaseModel):
    """Telemetry analysis input payload."""

    readings: list[ReadingInput] = Field(
        ..., min_length=1, description="Batch of sensor telemetry readings"
    )
    device_state: dict[str, Any] | None = Field(
        None, description="Optional persistent state dictionary from prior analysis"
    )
    device_id: UUID | None = Field(None, description="Optional registered device identifier")


class StageForecastSchema(BaseModel):
    """Stage-level prognostic remaining useful life forecast."""

    health_percent: float
    remaining_days: int | None
    band_low: int | None
    band_high: int | None
    status_text: str
    estimated: bool
    learning: bool


class DiagnosisSchema(BaseModel):
    """Explainable diagnostic alert."""

    fault_type: FaultType
    reason_code: str
    confidence: float
    evidence: dict[str, Any]
    human_text: str


class AnalyzeResponse(BaseModel):
    """Complete advisory analysis output with updated state for subsequent calls."""

    stages: dict[ConsumableType, StageForecastSchema]
    active_diagnoses: list[DiagnosisSchema]
    event_tags: list[EventType]
    is_lite_mode: bool
    device_tier: DeviceTier
    sensor_faults_detected: list[SensorFaultType]
    updated_device_state: dict[str, Any]
