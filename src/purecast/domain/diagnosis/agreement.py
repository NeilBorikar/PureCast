"""Two-indicator agreement engine for diagnostic alert confirmation.

To eliminate false alarms, alerts must be supported by at least TWO independent
physical indicators (e.g. flow drop + pressure rise). Never trigger on flow drop
alone if water temperature is cold.
"""

from purecast.domain.config import AlgorithmConfig
from purecast.domain.diagnosis.rules import Diagnosis
from purecast.domain.enums import FaultType
from purecast.domain.health.baseline import BaselineState
from purecast.domain.reading import SensorReading


def get_independent_indicators(
    fault_type: FaultType,
    reading: SensorReading,
    baseline: BaselineState,
    sediment_remaining_days: int | None = None,
    sediment_health: float = 100.0,
    config: AlgorithmConfig | None = None,
) -> list[str]:
    """Identify independent physical indicators supporting a suspected fault mode."""
    cfg = config or AlgorithmConfig()
    indicators: list[str] = []

    current_dp = 0.0
    if reading.pressure_p1 is not None and reading.pressure_p2 is not None:
        current_dp = max(0.0, reading.pressure_p1 - reading.pressure_p2)

    base_dp = max(baseline.prefilter_dp, 0.5)
    base_flow = max(baseline.flow_rate, 0.1)
    current_flow = reading.flow_rate if reading.flow_rate is not None else base_flow

    current_salt_passage = baseline.salt_passage
    if reading.tds_in is not None and reading.tds_out is not None and reading.tds_in > 0:
        current_salt_passage = reading.tds_out / reading.tds_in

    is_cold_water = (
        reading.temperature is not None and reading.temperature < cfg.cold_morning_temp_c
    )

    if fault_type == FaultType.PREFILTER_CLOG:
        # Indicator 1: Pressure drop increased across prefilter
        if current_dp > (base_dp * 1.05):
            indicators.append("PREFILTER_DP_ELEVATED")

        # Indicator 2: Flow rate depressed
        if current_flow < (base_flow * 0.95):
            indicators.append("FLOW_RATE_DEPRESSED")

        # Indicator 3: Sediment remaining life or health degraded
        if (
            sediment_remaining_days is not None and sediment_remaining_days < 90
        ) or sediment_health < 85.0:
            indicators.append("SEDIMENT_HEALTH_DECLINED")

    elif fault_type == FaultType.MEMBRANE_FOULING_SCALING:
        # Indicator 1: Permeate flow rate dropped
        # Do not count flow drop alone if temperature is cold without temperature compensation
        if current_flow < (base_flow * (1.0 - cfg.eol_flow_drop_fraction)):
            if not is_cold_water:
                indicators.append("PERMEATE_FLOW_DROPPED")
            else:
                # In cold water, only count if flow drop exceeds temperature viscosity expectation
                expected_temp_factor = 1.0 + cfg.temp_flow_coeff * (
                    reading.temperature - cfg.ref_temp_c
                )
                if current_flow < (base_flow * expected_temp_factor * 0.90):
                    indicators.append("PERMEATE_FLOW_DROPPED_TEMP_NORMALIZED")

        # Indicator 2: Salt rejection remains stable (distinguishes fouling from wear/tearing)
        if abs(current_salt_passage - baseline.salt_passage) < 0.03:
            indicators.append("SALT_REJECTION_STABLE")

        # Indicator 3: Feed pressure adequate (not starved)
        if (
            reading.pressure_p3 is not None
            and reading.pressure_p3 >= cfg.low_supply_pressure_psi
        ):
            indicators.append("FEED_PRESSURE_ADEQUATE")

    elif fault_type == FaultType.MEMBRANE_WEAR:
        # Indicator 1: Salt passage increased significantly
        if current_salt_passage > (baseline.salt_passage + 0.04):
            indicators.append("SALT_PASSAGE_ELEVATED")

        # Indicator 2: High permeate TDS in absolute terms
        if reading.tds_out is not None and reading.tds_out > 50.0:
            indicators.append("PERMEATE_TDS_HIGH")

        # Indicator 3: Flow maintained or higher (no membrane scaling blockage)
        if current_flow >= (base_flow * 0.90):
            indicators.append("PERMEATE_FLUX_UNBLOCKED")

    elif fault_type == FaultType.SUPPLY_FAULT:
        # Indicator 1: Feed pressure P3 below threshold
        if (
            reading.pressure_p3 is not None
            and reading.pressure_p3 < cfg.low_supply_pressure_psi
        ):
            indicators.append("FEED_PRESSURE_LOW")

        # Indicator 2: Prefilter dP normal (no blockage causing the drop)
        if current_dp <= cfg.prefilter_dp_normal_max_psi:
            indicators.append("PREFILTER_DP_NORMAL")

        # Indicator 3: Permeate flow reduced due to low inlet head
        if current_flow < (base_flow * 0.90):
            indicators.append("FLOW_HEAD_STARVATION")

    elif fault_type == FaultType.UV_LAMP_WEAKENING:
        # Indicator 1: UV current drift
        if reading.uv_current is not None:
            drift_frac = abs(reading.uv_current - cfg.uv_nominal_current_ma) / max(
                cfg.uv_nominal_current_ma, 1.0
            )
            if drift_frac >= cfg.uv_eol_current_drift_fraction:
                indicators.append("UV_CURRENT_DRIFT")

        # Indicator 2: Ballast current non-zero and stable drift
        if reading.uv_current is not None and reading.uv_current > 0:
            indicators.append("UV_BALLAST_POWERED")

    return indicators


def verify_agreement(
    diagnoses: list[Diagnosis],
    reading: SensorReading,
    baseline: BaselineState,
    sediment_remaining_days: int | None = None,
    sediment_health: float = 100.0,
    config: AlgorithmConfig | None = None,
) -> list[Diagnosis]:
    """Filter candidate diagnoses, requiring at least two independent indicators to agree."""
    cfg = config or AlgorithmConfig()
    confirmed: list[Diagnosis] = []

    for d in diagnoses:
        indicators = get_independent_indicators(
            fault_type=d.fault_type,
            reading=reading,
            baseline=baseline,
            sediment_remaining_days=sediment_remaining_days,
            sediment_health=sediment_health,
            config=cfg,
        )
        if len(indicators) >= 2:
            # Update evidence to include agreeing indicators
            ev = dict(d.evidence)
            ev["agreeing_indicators"] = indicators
            confirmed.append(
                Diagnosis(
                    fault_type=d.fault_type,
                    reason_code=d.reason_code,
                    confidence=d.confidence,
                    evidence=ev,
                    human_text=d.human_text,
                )
            )

    return confirmed
