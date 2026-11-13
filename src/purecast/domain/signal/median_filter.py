"""Rolling time-window median filter for telemetry signals."""

from collections.abc import Sequence
from datetime import timedelta
import statistics

from purecast.domain.config import AlgorithmConfig
from purecast.domain.reading import SensorReading


def _compute_field_median(
    readings: Sequence[SensorReading],
    field_name: str,
    fallback: float | None,
) -> float | None:
    vals = [
        getattr(r, field_name)
        for r in readings
        if getattr(r, field_name) is not None
    ]
    return statistics.median(vals) if vals else fallback


def apply_median_filter(
    readings: Sequence[SensorReading],
    config: AlgorithmConfig | None = None,
) -> list[SensorReading]:
    """Apply a rolling median filter over time window, active only when pump is running.

    Args:
        readings: Time-ordered list of sensor readings.
        config: Algorithm configuration containing median_window_seconds.

    Returns:
        New list of sensor readings with median-filtered values when pump was running.
    """
    if not readings:
        return []

    cfg = config or AlgorithmConfig()
    window_delta = timedelta(seconds=cfg.median_window_seconds)

    filtered_readings: list[SensorReading] = []

    for i, current in enumerate(readings):
        if not current.pump_running:
            filtered_readings.append(current)
            continue

        window_start = current.timestamp - window_delta

        # Collect preceding readings in the time window where pump was running
        window_readings: list[SensorReading] = []
        for j in range(i, -1, -1):
            cand = readings[j]
            if cand.timestamp < window_start:
                break
            if cand.pump_running:
                window_readings.append(cand)

        if not window_readings:
            filtered_readings.append(current)
            continue

        filtered_reading = SensorReading(
            timestamp=current.timestamp,
            pump_running=current.pump_running,
            pressure_p1=_compute_field_median(window_readings, "pressure_p1", current.pressure_p1),
            pressure_p2=_compute_field_median(window_readings, "pressure_p2", current.pressure_p2),
            pressure_p3=_compute_field_median(window_readings, "pressure_p3", current.pressure_p3),
            flow_rate=_compute_field_median(window_readings, "flow_rate", current.flow_rate),
            tds_in=_compute_field_median(window_readings, "tds_in", current.tds_in),
            tds_out=_compute_field_median(window_readings, "tds_out", current.tds_out),
            temperature=_compute_field_median(window_readings, "temperature", current.temperature),
            turbidity=_compute_field_median(window_readings, "turbidity", current.turbidity),
            uv_current=_compute_field_median(window_readings, "uv_current", current.uv_current),
            operating_mode=current.operating_mode,
            device_tier=current.device_tier,
        )
        filtered_readings.append(filtered_reading)

    return filtered_readings
