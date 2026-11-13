"""Sanity checks flagging sensor instrumentation faults and removing invalid data."""

from collections.abc import Sequence
from dataclasses import dataclass, field

from purecast.domain.config import AlgorithmConfig
from purecast.domain.enums import DeviceTier, SensorFaultType
from purecast.domain.reading import SensorReading


@dataclass
class SanityCheckResult:
    """Outcome of sanity checking a sequence of readings."""

    valid_readings: list[SensorReading]
    faults: list[list[SensorFaultType]] = field(default_factory=list)

    @property
    def has_faults(self) -> bool:
        return any(bool(f) for f in self.faults)


def check_reading_sanity(
    reading: SensorReading,
    recent_history: Sequence[SensorReading] = (),
    config: AlgorithmConfig | None = None,
) -> list[SensorFaultType]:
    """Inspect a single reading against physical laws and instrument constraints."""
    cfg = config or AlgorithmConfig()
    faults: list[SensorFaultType] = []

    # 1. TDS Inversion: Permeate TDS cannot exceed feed water TDS
    if (
        reading.tds_in is not None
        and reading.tds_out is not None
        and reading.tds_out > (reading.tds_in + cfg.tds_inversion_tolerance)
    ):
        faults.append(SensorFaultType.TDS_INVERSION)

    # 2. Flow while pump off: Leakage or erroneous flow meter
    if (
        not reading.pump_running
        and reading.flow_rate is not None
        and reading.flow_rate > cfg.flow_while_pump_off_threshold
    ):
        faults.append(SensorFaultType.FLOW_WHILE_PUMP_OFF)

    # 3. Out-of-range checks
    out_of_range = False
    if reading.tds_in is not None and not (cfg.min_tds <= reading.tds_in <= cfg.max_tds):
        out_of_range = True
    if reading.tds_out is not None and not (cfg.min_tds <= reading.tds_out <= cfg.max_tds):
        out_of_range = True
    if reading.flow_rate is not None and not (cfg.min_flow <= reading.flow_rate <= cfg.max_flow):
        out_of_range = True
    if reading.temperature is not None and not (
        cfg.min_temp_c <= reading.temperature <= cfg.max_temp_c
    ):
        out_of_range = True
    if reading.pressure_p1 is not None and not (
        cfg.min_pressure <= reading.pressure_p1 <= cfg.max_pressure
    ):
        out_of_range = True
    if reading.pressure_p2 is not None and not (
        cfg.min_pressure <= reading.pressure_p2 <= cfg.max_pressure
    ):
        out_of_range = True
    if reading.pressure_p3 is not None and not (
        cfg.min_pressure <= reading.pressure_p3 <= cfg.max_pressure
    ):
        out_of_range = True
    if reading.turbidity is not None and not (
        cfg.min_turbidity <= reading.turbidity <= cfg.max_turbidity
    ):
        out_of_range = True
    if reading.uv_current is not None and not (
        cfg.min_uv_current <= reading.uv_current <= cfg.max_uv_current
    ):
        out_of_range = True

    if out_of_range:
        faults.append(SensorFaultType.OUT_OF_RANGE)

    # 4. Missing sensor dropout in FULL tier
    if reading.device_tier == DeviceTier.FULL:
        essential_sensors = [
            reading.pressure_p1,
            reading.flow_rate,
            reading.tds_in,
            reading.tds_out,
            reading.temperature,
        ]
        if any(v is None for v in essential_sensors):
            faults.append(SensorFaultType.SENSOR_DROPOUT)

    # 5. Frozen value check across recent samples
    if (
        len(recent_history) >= cfg.frozen_samples_threshold
        and reading.pump_running
        and reading.flow_rate is not None
    ):
        last_flows = [
            r.flow_rate
            for r in recent_history[-cfg.frozen_samples_threshold :]
            if r.flow_rate is not None
        ]
        if (
            len(last_flows) == cfg.frozen_samples_threshold
            and len(set(last_flows)) == 1
            and last_flows[0] == reading.flow_rate
        ):
            faults.append(SensorFaultType.FROZEN_VALUE)

    return faults


def validate_readings(
    readings: Sequence[SensorReading],
    config: AlgorithmConfig | None = None,
) -> SanityCheckResult:
    """Run sanity checks over a batch of readings, collecting faults and dropping corrupt data."""
    cfg = config or AlgorithmConfig()
    valid: list[SensorReading] = []
    all_faults: list[list[SensorFaultType]] = []

    for i, r in enumerate(readings):
        history = readings[max(0, i - cfg.frozen_samples_threshold) : i]
        faults = check_reading_sanity(r, history, cfg)
        all_faults.append(faults)

        # Drop reading if invalid (e.g. TDS inversion, out of range, flow while pump off)
        fatal_faults = {
            SensorFaultType.TDS_INVERSION,
            SensorFaultType.FLOW_WHILE_PUMP_OFF,
            SensorFaultType.OUT_OF_RANGE,
            SensorFaultType.FROZEN_VALUE,
        }
        if not any(f in fatal_faults for f in faults):
            valid.append(r)

    return SanityCheckResult(valid_readings=valid, faults=all_faults)
