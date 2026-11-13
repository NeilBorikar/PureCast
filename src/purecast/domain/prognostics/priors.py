"""Physics-based degradation priors per purifier stage."""

from purecast.domain.config import AlgorithmConfig
from purecast.domain.enums import ConsumableType, OperatingMode
from purecast.domain.health.load_model import get_mode_ageing_multiplier


def get_stage_nominal_days(stage: ConsumableType, config: AlgorithmConfig | None = None) -> float:
    """Return nominal design lifespan in days under standard operating conditions."""
    cfg = config or AlgorithmConfig()
    mapping = {
        ConsumableType.SEDIMENT: cfg.nominal_days_sediment,
        ConsumableType.CARBON: cfg.nominal_days_carbon,
        ConsumableType.MEMBRANE_PROTECTOR: cfg.nominal_days_protector,
        ConsumableType.RO_MEMBRANE: cfg.nominal_days_ro,
        ConsumableType.UV_LAMP: cfg.nominal_days_uv,
    }
    return mapping.get(stage, 365.0)


def compute_prior_ageing_rate(
    stage: ConsumableType,
    inlet_tds: float = 500.0,
    turbidity: float = 1.0,
    liters_per_day: float = 20.0,
    mode: OperatingMode = OperatingMode.RO,
    config: AlgorithmConfig | None = None,
) -> float:
    """Calculate physics-prior degradation rate in percent per day (negative value).

    Higher TDS, higher turbidity, and higher volumetric usage accelerate degradation.
    """
    cfg = config or AlgorithmConfig()
    nominal_days = get_stage_nominal_days(stage, cfg)

    # Stress factors
    tds_stress = max(0.2, inlet_tds / max(cfg.carbon_ref_tds, 1.0))
    turbidity_stress = max(1.0, turbidity / max(cfg.carbon_ref_turbidity, 0.1))
    flow_stress = max(0.1, liters_per_day / 20.0)
    mode_stress = get_mode_ageing_multiplier(mode, cfg)

    if stage == ConsumableType.SEDIMENT:
        total_stress = turbidity_stress * flow_stress * mode_stress
    elif stage in (ConsumableType.CARBON, ConsumableType.MEMBRANE_PROTECTOR):
        total_stress = tds_stress * turbidity_stress * flow_stress * mode_stress
    elif stage == ConsumableType.RO_MEMBRANE:
        total_stress = tds_stress * flow_stress * mode_stress
    else:  # UV_LAMP
        total_stress = mode_stress

    effective_lifespan_days = max(10.0, nominal_days / max(total_stress, 0.1))
    daily_rate = -100.0 / effective_lifespan_days
    return round(daily_rate, 4)

