"""Contextual event detection and false-alarm suppression.

Tags operational windows with environmental or usage context:
- COLD_WATER_MORNING: Water temperature < 18 °C (viscosity naturally restricts permeate flow).
- HOLIDAY: Extended inactivity (no flow for >= 3 days).
- POWER_CUT: Device power disruption or total electrical shutdown.

Suppresses false-positive alarms during tagged event windows.
"""

from collections.abc import Sequence
from datetime import timedelta

from purecast.domain.config import AlgorithmConfig
from purecast.domain.diagnosis.rules import Diagnosis
from purecast.domain.enums import EventType, FaultType
from purecast.domain.reading import SensorReading


def tag_reading_events(
    readings: Sequence[SensorReading],
    config: AlgorithmConfig | None = None,
    days_inactive: float = 0.0,
) -> list[EventType]:
    """Detect contextual external events across readings and history."""
    cfg = config or AlgorithmConfig()
    events: list[EventType] = []

    if not readings:
        return events

    latest = readings[-1]

    # 1. COLD_WATER_MORNING: Temperature < 18 °C
    if latest.temperature is not None and latest.temperature < cfg.cold_morning_temp_c:
        events.append(EventType.COLD_WATER_MORNING)

    # 2. HOLIDAY: No flow for >= 3 days
    if days_inactive >= cfg.holiday_inactivity_days:
        events.append(EventType.HOLIDAY)
    elif len(readings) >= 2:
        time_span = latest.timestamp - readings[0].timestamp
        if time_span >= timedelta(days=cfg.holiday_inactivity_days):
            all_no_flow = all(
                (r.flow_rate is None or r.flow_rate <= 0.01) and not r.pump_running
                for r in readings
            )
            if all_no_flow:
                events.append(EventType.HOLIDAY)

    # 3. POWER_CUT: Electrical shutdown or loss of power state
    # Detected when pump is off, UV current is 0, and sensors show dropout or unpowered state
    if (
        not latest.pump_running
        and (latest.uv_current is None or latest.uv_current == 0.0)
        and (latest.flow_rate is None or latest.flow_rate == 0.0)
        and any(r.pump_running for r in readings[:-1])
        and latest.uv_current == 0.0
    ):
        events.append(EventType.POWER_CUT)

    return events


def filter_suppressed_diagnoses(
    diagnoses: list[Diagnosis],
    events: Sequence[EventType],
) -> list[Diagnosis]:
    """Filter out diagnoses that should be suppressed during detected events."""
    event_set = set(events)
    if not event_set:
        return list(diagnoses)

    retained: list[Diagnosis] = []

    for diag in diagnoses:
        # COLD_WATER_MORNING: Suppress false membrane fouling alarms
        if (
            EventType.COLD_WATER_MORNING in event_set
            and diag.fault_type == FaultType.MEMBRANE_FOULING_SCALING
        ):
            continue

        # HOLIDAY: Suppress usage-dependent alarms
        if EventType.HOLIDAY in event_set and diag.fault_type in (
            FaultType.PREFILTER_CLOG,
            FaultType.MEMBRANE_FOULING_SCALING,
        ):
            continue

        # POWER_CUT: Suppress all filter failure diagnoses
        if EventType.POWER_CUT in event_set:
            continue

        retained.append(diag)

    return retained
