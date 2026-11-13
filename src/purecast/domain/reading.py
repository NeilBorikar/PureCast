"""Pure domain representation of purifier telemetry sensor readings."""

from dataclasses import dataclass
from datetime import datetime

from purecast.domain.enums import DeviceTier, OperatingMode


@dataclass(frozen=True)
class SensorReading:
    """Raw or filtered sensor telemetry reading from edge purifier."""

    timestamp: datetime
    pump_running: bool
    pressure_p1: float | None = None
    pressure_p2: float | None = None
    pressure_p3: float | None = None
    flow_rate: float | None = None
    tds_in: float | None = None
    tds_out: float | None = None
    temperature: float | None = None
    turbidity: float | None = None
    uv_current: float | None = None
    operating_mode: OperatingMode = OperatingMode.RO
    device_tier: DeviceTier = DeviceTier.FULL

