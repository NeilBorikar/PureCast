"""Health Index calculation for all five purifier stages."""

from dataclasses import dataclass

from purecast.domain.config import AlgorithmConfig
from purecast.domain.enums import ConsumableType
from purecast.domain.health.baseline import BaselineState
from purecast.domain.health.eol_lines import EOLLimits
from purecast.domain.reading import SensorReading


@dataclass(frozen=True)
class HealthIndices:
    """Stage health percentages (0.0% to 100.0%)."""

    sediment: float
    carbon: float
    membrane_protector: float
    ro_membrane: float
    uv_lamp: float

    def as_dict(self) -> dict[ConsumableType, float]:
        return {
            ConsumableType.SEDIMENT: self.sediment,
            ConsumableType.CARBON: self.carbon,
            ConsumableType.MEMBRANE_PROTECTOR: self.membrane_protector,
            ConsumableType.RO_MEMBRANE: self.ro_membrane,
            ConsumableType.UV_LAMP: self.uv_lamp,
        }


def compute_stage_health_indices(
    reading: SensorReading,
    baseline: BaselineState,
    run_hours: float = 0.0,
    config: AlgorithmConfig | None = None,
) -> HealthIndices:
    """Compute per-stage Health Index (100% new, 0% at EOL, clamped 0-100)."""
    cfg = config or AlgorithmConfig()
    eol = EOLLimits.from_config(cfg)

    # 1. Pre-filter pressure drop (P1 - P2)
    current_dp = 0.0
    if reading.pressure_p1 is not None and reading.pressure_p2 is not None:
        current_dp = max(0.0, reading.pressure_p1 - reading.pressure_p2)
    elif baseline.prefilter_dp > 0:
        current_dp = baseline.prefilter_dp

    base_dp = max(baseline.prefilter_dp, 0.5)
    dp_rise_amount = max(0.0, current_dp - base_dp)
    max_allowable_dp_rise = base_dp * eol.prefilter_dp_rise_fraction

    # Sediment health from dP rise
    if max_allowable_dp_rise > 0:
        sediment_health = 100.0 * (1.0 - (dp_rise_amount / max_allowable_dp_rise))
    else:
        sediment_health = 100.0
    sediment_health = max(0.0, min(100.0, sediment_health))

    # Carbon health from dP and protector
    carbon_health = sediment_health
    membrane_protector_health = sediment_health

    # 2. RO Membrane health: worse of normalized flow drop and salt passage rise
    # a) Flow drop
    base_flow = max(baseline.flow_rate, 0.1)
    current_flow = reading.flow_rate if reading.flow_rate is not None else base_flow
    flow_drop = max(0.0, base_flow - current_flow)
    max_allowable_flow_drop = base_flow * eol.flow_drop_fraction

    if max_allowable_flow_drop > 0:
        health_flow = 100.0 * (1.0 - (flow_drop / max_allowable_flow_drop))
    else:
        health_flow = 100.0

    # b) Salt passage rise
    base_salt_passage = max(baseline.salt_passage, 0.001)
    current_salt_passage = base_salt_passage
    if reading.tds_in is not None and reading.tds_out is not None and reading.tds_in > 0:
        current_salt_passage = reading.tds_out / reading.tds_in

    salt_passage_rise = max(0.0, current_salt_passage - base_salt_passage)
    if eol.salt_passage_rise > 0:
        health_salt = 100.0 * (1.0 - (salt_passage_rise / eol.salt_passage_rise))
    else:
        health_salt = 100.0

    ro_health = max(0.0, min(100.0, health_flow, health_salt))

    # 3. UV Lamp health from current drift and run-hours
    uv_curr = reading.uv_current if reading.uv_current is not None else cfg.uv_nominal_current_ma
    current_drift_frac = abs(uv_curr - cfg.uv_nominal_current_ma) / max(
        cfg.uv_nominal_current_ma, 1.0
    )
    health_current = 100.0 * (1.0 - (current_drift_frac / eol.uv_current_drift_fraction))

    hours_fraction = run_hours / max(eol.uv_max_hours, 1.0)
    health_hours = 100.0 * (1.0 - hours_fraction)

    uv_health = max(0.0, min(100.0, health_current, health_hours))

    return HealthIndices(
        sediment=round(sediment_health, 2),
        carbon=round(carbon_health, 2),
        membrane_protector=round(membrane_protector_health, 2),
        ro_membrane=round(ro_health, 2),
        uv_lamp=round(uv_health, 2),
    )
