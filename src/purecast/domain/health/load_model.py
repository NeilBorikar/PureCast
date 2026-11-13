"""Load-based degradation and operating mode ageing model."""

from dataclasses import dataclass

from purecast.domain.config import AlgorithmConfig
from purecast.domain.enums import OperatingMode


def get_mode_ageing_multiplier(
    mode: OperatingMode,
    config: AlgorithmConfig | None = None,
) -> float:
    """Return physics-based ageing rate multiplier for operating mode."""
    cfg = config or AlgorithmConfig()
    if mode == OperatingMode.RO:
        return cfg.ageing_multiplier_ro
    if mode == OperatingMode.UF_UV:
        return cfg.ageing_multiplier_uf_uv
    if mode == OperatingMode.VACAY:
        return cfg.ageing_multiplier_vacay
    return 1.0


@dataclass
class CarbonLoadEstimate:
    """Estimate for Carbon stage remaining capacity and health index."""

    health_percentage: float
    equivalent_liters_used: float
    rated_capacity_liters: float
    estimated: bool = True


def estimate_carbon_health_from_load(
    cumulative_liters: float,
    avg_inlet_tds: float = 500.0,
    avg_turbidity: float = 1.0,
    mode: OperatingMode = OperatingMode.RO,
    config: AlgorithmConfig | None = None,
) -> CarbonLoadEstimate:
    """Compute load-based degradation estimate for activated carbon filter.

    Load factor = (inlet_tds / ref_tds) * max(1.0, turbidity / ref_turbidity) * mode_multiplier
    """
    cfg = config or AlgorithmConfig()

    tds_ratio = max(0.1, avg_inlet_tds / max(cfg.carbon_ref_tds, 1.0))
    turbidity_factor = max(1.0, avg_turbidity / max(cfg.carbon_ref_turbidity, 0.1))
    mode_multiplier = get_mode_ageing_multiplier(mode, cfg)

    # Equivalent stress liters
    stress_liters = cumulative_liters * tds_ratio * turbidity_factor * mode_multiplier
    fraction_consumed = stress_liters / max(cfg.carbon_rated_liters, 1.0)
    health_pct = max(0.0, min(100.0, 100.0 * (1.0 - fraction_consumed)))

    return CarbonLoadEstimate(
        health_percentage=round(health_pct, 2),
        equivalent_liters_used=round(stress_liters, 1),
        rated_capacity_liters=cfg.carbon_rated_liters,
        estimated=True,
    )

