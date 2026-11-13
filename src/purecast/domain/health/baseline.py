"""New-state baseline tracking per device."""

import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from purecast.domain.config import AlgorithmConfig
from purecast.domain.reading import SensorReading


@dataclass
class BaselineState:
    """Per-unit established baseline representing 100% new-state health."""

    flow_rate: float = 1.0
    salt_passage: float = 0.02
    prefilter_dp: float = 5.0
    uv_current: float = 400.0
    feed_pressure_p3: float = 40.0
    sample_count: int = 0
    is_established: bool = False

    def to_dict(self) -> dict[str, float | int | bool]:
        """Serialize for persistence."""
        return {
            "flow_rate": self.flow_rate,
            "salt_passage": self.salt_passage,
            "prefilter_dp": self.prefilter_dp,
            "uv_current": self.uv_current,
            "feed_pressure_p3": self.feed_pressure_p3,
            "sample_count": self.sample_count,
            "is_established": self.is_established,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "BaselineState":
        """Deserialize from persistence dict."""
        return cls(
            flow_rate=float(data.get("flow_rate", 1.0)),  # type: ignore[arg-type]
            salt_passage=float(data.get("salt_passage", 0.02)),  # type: ignore[arg-type]
            prefilter_dp=float(data.get("prefilter_dp", 5.0)),  # type: ignore[arg-type]
            uv_current=float(data.get("uv_current", 400.0)),  # type: ignore[arg-type]
            feed_pressure_p3=float(data.get("feed_pressure_p3", 40.0)),  # type: ignore[arg-type]
            sample_count=int(data.get("sample_count", 0)),  # type: ignore[arg-type]
            is_established=bool(data.get("is_established", False)),
        )


def compute_baseline(
    readings: Sequence[SensorReading],
    config: AlgorithmConfig | None = None,
    existing: BaselineState | None = None,
) -> BaselineState:
    """Compute or update the new-state baseline from valid operational readings."""
    cfg = config or AlgorithmConfig()
    base = existing or BaselineState()

    if base.is_established:
        return base

    valid_pump_readings = [r for r in readings if r.pump_running]
    if not valid_pump_readings:
        return base

    flows: list[float] = []
    salt_passages: list[float] = []
    dps: list[float] = []
    uv_currents: list[float] = []
    p3s: list[float] = []

    for r in valid_pump_readings:
        if r.flow_rate is not None and r.flow_rate > 0.0:
            flows.append(r.flow_rate)
        if r.tds_in is not None and r.tds_out is not None and r.tds_in > 0.0:
            salt_passages.append(r.tds_out / r.tds_in)
        if r.pressure_p1 is not None and r.pressure_p2 is not None:
            dps.append(max(0.0, r.pressure_p1 - r.pressure_p2))
        if r.uv_current is not None and r.uv_current > 0.0:
            uv_currents.append(r.uv_current)
        if r.pressure_p3 is not None and r.pressure_p3 > 0.0:
            p3s.append(r.pressure_p3)

    total_samples = base.sample_count + len(valid_pump_readings)

    # If we have enough samples, compute medians
    if flows:
        base.flow_rate = statistics.median(flows)
    if salt_passages:
        base.salt_passage = statistics.median(salt_passages)
    if dps:
        base.prefilter_dp = statistics.median(dps)
    if uv_currents:
        base.uv_current = statistics.median(uv_currents)
    if p3s:
        base.feed_pressure_p3 = statistics.median(p3s)

    base.sample_count = total_samples
    if base.sample_count >= cfg.baseline_sample_count:
        base.is_established = True

    return base
