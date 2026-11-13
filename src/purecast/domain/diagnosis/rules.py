"""Explainable rule engine for diagnosing purifier failure modes."""

from dataclasses import dataclass
from typing import Any

from purecast.domain.config import AlgorithmConfig
from purecast.domain.enums import FaultType
from purecast.domain.health.baseline import BaselineState
from purecast.domain.reading import SensorReading


@dataclass(frozen=True)
class Diagnosis:
    """Diagnostic outcome with explainable root cause and evidence."""

    fault_type: FaultType
    reason_code: str
    confidence: float  # 0.0 to 1.0
    evidence: dict[str, Any]
    human_text: str


def evaluate_rules(
    reading: SensorReading,
    baseline: BaselineState,
    sediment_remaining_days: int | None = None,
    sediment_health: float = 100.0,
    config: AlgorithmConfig | None = None,
) -> list[Diagnosis]:
    """Execute diagnosis rule engine against current telemetry and baseline."""
    cfg = config or AlgorithmConfig()
    diagnoses: list[Diagnosis] = []

    # Calculate key physical parameters
    current_dp = 0.0
    if reading.pressure_p1 is not None and reading.pressure_p2 is not None:
        current_dp = max(0.0, reading.pressure_p1 - reading.pressure_p2)

    current_salt_passage = baseline.salt_passage
    if reading.tds_in is not None and reading.tds_out is not None and reading.tds_in > 0:
        current_salt_passage = reading.tds_out / reading.tds_in

    base_flow = max(baseline.flow_rate, 0.1)
    current_flow = reading.flow_rate if reading.flow_rate is not None else base_flow

    # 1. SUPPLY_FAULT: feed pressure P3 low while pre-filter dP normal
    # Checked first because low supply pressure alters downstream readings
    if (
        reading.pressure_p3 is not None
        and reading.pressure_p3 < cfg.low_supply_pressure_psi
        and current_dp <= cfg.prefilter_dp_normal_max_psi
    ):
        diagnoses.append(
            Diagnosis(
                fault_type=FaultType.SUPPLY_FAULT,
                reason_code="FEED_PRESSURE_LOW_DP_NORMAL",
                confidence=0.92,
                evidence={
                    "pressure_p3": reading.pressure_p3,
                    "threshold_p3": cfg.low_supply_pressure_psi,
                    "prefilter_dp": current_dp,
                },
                human_text="Supply problem, not a filter problem",
            )
        )

    # 2. PREFILTER_CLOG: pressure drop rising AND sediment forecast shrinking
    dp_elevated = current_dp > (baseline.prefilter_dp * 1.05)
    sediment_stressed = (
        (sediment_remaining_days is not None and sediment_remaining_days < 90)
        or sediment_health < 85.0
    )
    if dp_elevated and sediment_stressed:
        confidence = min(0.95, 0.70 + (current_dp - baseline.prefilter_dp) * 0.05)
        diagnoses.append(
            Diagnosis(
                fault_type=FaultType.PREFILTER_CLOG,
                reason_code="DP_RISING_SEDIMENT_DECLINING",
                confidence=round(confidence, 2),
                evidence={
                    "current_dp": current_dp,
                    "baseline_dp": baseline.prefilter_dp,
                    "sediment_health": sediment_health,
                    "sediment_remaining_days": sediment_remaining_days,
                },
                human_text=(
                    "Prefilter cartridge clogged with sediment, causing "
                    "high pressure drop across stage 1."
                ),
            )
        )

    # 3. MEMBRANE_FOULING_SCALING: normalized flow falling while salt passage stable
    flow_dropped = current_flow < (base_flow * 0.92)
    salt_passage_stable = abs(current_salt_passage - baseline.salt_passage) < 0.03
    if flow_dropped and salt_passage_stable:
        confidence = min(0.95, 0.75 + (base_flow - current_flow) / base_flow)
        diagnoses.append(
            Diagnosis(
                fault_type=FaultType.MEMBRANE_FOULING_SCALING,
                reason_code="FLOW_DROP_STABLE_REJECTION",
                confidence=round(confidence, 2),
                evidence={
                    "current_flow": current_flow,
                    "baseline_flow": base_flow,
                    "current_salt_passage": current_salt_passage,
                    "baseline_salt_passage": baseline.salt_passage,
                },
                human_text=(
                    "Membrane fouling or mineral scaling: permeate flow rate is "
                    "depressed while salt rejection remains stable."
                ),
            )
        )

    # 4. MEMBRANE_WEAR: salt passage rising
    if current_salt_passage > (baseline.salt_passage + 0.04):
        confidence = min(
            0.98,
            0.70 + (current_salt_passage - baseline.salt_passage) / 0.08 * 0.25,
        )
        diagnoses.append(
            Diagnosis(
                fault_type=FaultType.MEMBRANE_WEAR,
                reason_code="SALT_PASSAGE_ELEVATED",
                confidence=round(confidence, 2),
                evidence={
                    "current_salt_passage": current_salt_passage,
                    "baseline_salt_passage": baseline.salt_passage,
                    "tds_in": reading.tds_in,
                    "tds_out": reading.tds_out,
                },
                human_text=(
                    "RO membrane physical wear or micro-breach: salt passage "
                    "has increased significantly above baseline."
                ),
            )
        )

    # 5. UV_LAMP_WEAKENING: lamp current drift
    if reading.uv_current is not None:
        drift_frac = abs(reading.uv_current - cfg.uv_nominal_current_ma) / max(
            cfg.uv_nominal_current_ma, 1.0
        )
        if drift_frac >= 0.15:
            confidence = min(0.95, 0.70 + drift_frac)
            diagnoses.append(
                Diagnosis(
                    fault_type=FaultType.UV_LAMP_WEAKENING,
                    reason_code="UV_CURRENT_DRIFT",
                    confidence=round(confidence, 2),
                    evidence={
                        "uv_current": reading.uv_current,
                        "nominal_current": cfg.uv_nominal_current_ma,
                        "drift_fraction": round(drift_frac, 3),
                    },
                    human_text=(
                        "UV disinfection lamp ballast/tube current drift indicates "
                        "weakening germicidal radiation intensity."
                    ),
                )
            )

    return diagnoses
