"""Pure domain advisory analysis pipeline for PureCast water purifiers.

Orchestrates:
1. Telemetry sanity checks and sensor fault filtering.
2. Rolling median filtering and physics-based temperature/pressure normalization.
3. Operating event detection (power cuts, holidays, cold morning).
4. Per-unit baseline learning.
5. Multi-stage Health Index computation.
6. Kalman filter degradation tracking and RUL forecasting.
7. Explainable diagnostic rule evaluation with 2-indicator agreement and hysteresis.
8. LITE tier fallback estimation via load-based modeling.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from purecast.domain.config import AlgorithmConfig
from purecast.domain.diagnosis.agreement import verify_agreement
from purecast.domain.diagnosis.event_tagging import filter_suppressed_diagnoses, tag_reading_events
from purecast.domain.diagnosis.hysteresis import HysteresisState, HysteresisTracker
from purecast.domain.diagnosis.rules import Diagnosis, evaluate_rules
from purecast.domain.enums import (
    ConsumableType,
    DeviceTier,
    EventType,
    OperatingMode,
    SensorFaultType,
)
from purecast.domain.health.baseline import BaselineState, compute_baseline
from purecast.domain.health.health_index import compute_stage_health_indices
from purecast.domain.health.load_model import estimate_carbon_health_from_load
from purecast.domain.prognostics.kalman import KalmanState, TwoStateKalmanFilter
from purecast.domain.prognostics.priors import compute_prior_ageing_rate
from purecast.domain.prognostics.remaining_life import calculate_remaining_life
from purecast.domain.reading import SensorReading
from purecast.domain.signal.median_filter import apply_median_filter
from purecast.domain.signal.sanity_checks import validate_readings
from purecast.domain.signal.temperature_correction import (
    normalize_flow_feed_pressure,
    normalize_flow_temperature,
)


@dataclass
class StageForecast:
    """Prognostic forecast for an individual consumable stage."""

    health_percent: float
    remaining_days: int | None
    band_low: int | None
    band_high: int | None
    status_text: str
    estimated: bool
    learning: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "health_percent": self.health_percent,
            "remaining_days": self.remaining_days,
            "band_low": self.band_low,
            "band_high": self.band_high,
            "status_text": self.status_text,
            "estimated": self.estimated,
            "learning": self.learning,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> "StageForecast":
        rem_days = (
            int(d["remaining_days"]) if d.get("remaining_days") is not None else None
        )
        return cls(
            health_percent=float(d.get("health_percent", 100.0)),  # type: ignore[arg-type]
            remaining_days=rem_days,
            band_low=int(d["band_low"]) if d.get("band_low") is not None else None,
            band_high=int(d["band_high"]) if d.get("band_high") is not None else None,
            status_text=str(d.get("status_text", "Operational")),
            estimated=bool(d.get("estimated", False)),
            learning=bool(d.get("learning", False)),
        )


@dataclass
class AnalysisResult:
    """Complete diagnostic and prognostic evaluation output."""

    stages: dict[ConsumableType, StageForecast]
    active_diagnoses: list[Diagnosis]
    event_tags: list[EventType]
    is_lite_mode: bool
    device_tier: DeviceTier
    sensor_faults_detected: list[SensorFaultType] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "stages": {k.value: v.to_dict() for k, v in self.stages.items()},
            "active_diagnoses": [
                {
                    "fault_type": d.fault_type.value,
                    "reason_code": d.reason_code,
                    "confidence": d.confidence,
                    "evidence": d.evidence,
                    "human_text": d.human_text,
                }
                for d in self.active_diagnoses
            ],
            "event_tags": [e.value for e in self.event_tags],
            "is_lite_mode": self.is_lite_mode,
            "device_tier": self.device_tier.value,
            "sensor_faults_detected": [f.value for f in self.sensor_faults_detected],
        }


@dataclass
class DeviceState:
    """Stateful device tracker carrying historical baselines and Kalman filters across runs."""

    kalman_states: dict[str, KalmanState] = field(default_factory=dict)
    baseline: BaselineState = field(default_factory=BaselineState)
    hysteresis: HysteresisState = field(default_factory=HysteresisState)
    install_date: datetime | None = None
    total_liters_processed: float = 0.0
    total_pump_hours: float = 0.0
    last_processed_timestamp: datetime | None = None
    device_tier: DeviceTier = DeviceTier.FULL

    def to_dict(self) -> dict[str, object]:
        return {
            "kalman_states": {k: v.to_dict() for k, v in self.kalman_states.items()},
            "baseline": self.baseline.to_dict(),
            "hysteresis": self.hysteresis.to_dict(),
            "install_date": self.install_date.isoformat() if self.install_date else None,
            "total_liters_processed": self.total_liters_processed,
            "total_pump_hours": self.total_pump_hours,
            "last_processed_timestamp": (
                self.last_processed_timestamp.isoformat()
                if self.last_processed_timestamp
                else None
            ),
            "device_tier": self.device_tier.value,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> "DeviceState":
        raw_kalman = d.get("kalman_states", {})
        kalman_states: dict[str, KalmanState] = {}
        if isinstance(raw_kalman, dict):
            for k, v in raw_kalman.items():
                if isinstance(v, dict):
                    kalman_states[str(k)] = KalmanState.from_dict(v)

        raw_base = d.get("baseline", {})
        baseline = (
            BaselineState.from_dict(raw_base)  # type: ignore[arg-type]
            if isinstance(raw_base, dict)
            else BaselineState()
        )

        raw_hyst = d.get("hysteresis", {})
        hysteresis = (
            HysteresisState.from_dict(raw_hyst)  # type: ignore[arg-type]
            if isinstance(raw_hyst, dict)
            else HysteresisState()
        )

        install_dt = None
        if d.get("install_date"):
            install_dt = datetime.fromisoformat(str(d["install_date"]))

        last_dt = None
        if d.get("last_processed_timestamp"):
            last_dt = datetime.fromisoformat(str(d["last_processed_timestamp"]))

        tier_str = str(d.get("device_tier", DeviceTier.FULL.value))
        tier = (
            DeviceTier(tier_str)
            if tier_str in DeviceTier._value2member_map_
            else DeviceTier.FULL
        )

        return cls(
            kalman_states=kalman_states,
            baseline=baseline,
            hysteresis=hysteresis,
            install_date=install_dt,
            total_liters_processed=float(d.get("total_liters_processed", 0.0)),  # type: ignore[arg-type]
            total_pump_hours=float(d.get("total_pump_hours", 0.0)),  # type: ignore[arg-type]
            last_processed_timestamp=last_dt,
            device_tier=tier,
        )


def analyze(
    device_state: DeviceState | None,
    readings: Sequence[SensorReading],
    config: AlgorithmConfig | None = None,
) -> tuple[AnalysisResult, DeviceState]:
    """Execute end-to-end PureCast analysis pipeline over a batch of telemetry readings."""
    cfg = config or AlgorithmConfig()
    state = device_state or DeviceState()

    all_stages = [
        ConsumableType.SEDIMENT,
        ConsumableType.CARBON,
        ConsumableType.MEMBRANE_PROTECTOR,
        ConsumableType.RO_MEMBRANE,
        ConsumableType.UV_LAMP,
    ]

    # Initialize Kalman states for stages if not yet present
    for stg in all_stages:
        if stg.value not in state.kalman_states:
            prior_rate = compute_prior_ageing_rate(stg, config=cfg)
            state.kalman_states[stg.value] = KalmanState(
                health=100.0,
                rate=prior_rate,
                p00=cfg.kalman_initial_p_health,
                p11=cfg.kalman_initial_p_rate,
            )

    if not readings:
        # No readings provided; return current state forecasts
        current_forecasts: dict[ConsumableType, StageForecast] = {}
        for stg in all_stages:
            kstate = state.kalman_states[stg.value]
            now_dt = (
                datetime.now(tz=state.install_date.tzinfo)
                if state.install_date and state.install_date.tzinfo
                else datetime.now(tz=UTC)
            )
            days_inst = (
                (now_dt - state.install_date).total_seconds() / 86400.0
                if state.install_date
                else 30.0
            )
            rl = calculate_remaining_life(kstate, days_inst, cfg)
            current_forecasts[stg] = StageForecast(
                health_percent=round(kstate.health, 2),
                remaining_days=rl.remaining_days,
                band_low=rl.band_low,
                band_high=rl.band_high,
                status_text=rl.status_text,
                estimated=rl.estimated,
                learning=rl.learning,
            )
        return (
            AnalysisResult(
                stages=current_forecasts,
                active_diagnoses=[],
                event_tags=[],
                is_lite_mode=(state.device_tier == DeviceTier.LITE),
                device_tier=state.device_tier,
                sensor_faults_detected=[],
            ),
            state,
        )

    # Sort readings chronologically
    sorted_readings = sorted(readings, key=lambda r: r.timestamp)
    first_reading = sorted_readings[0]
    last_reading = sorted_readings[-1]

    if state.install_date is None:
        state.install_date = first_reading.timestamp

    # Determine Device Tier and LITE mode fallback
    is_explicit_lite = (
        state.device_tier == DeviceTier.LITE
        or any(r.device_tier == DeviceTier.LITE for r in sorted_readings)
    )
    has_no_pressure_sensors = all(
        r.pressure_p1 is None and r.pressure_p2 is None and r.pressure_p3 is None
        for r in sorted_readings
    )
    is_lite_mode = is_explicit_lite or has_no_pressure_sensors
    active_tier = DeviceTier.LITE if is_lite_mode else DeviceTier.FULL
    state.device_tier = active_tier

    # 1. Sanity Checks & Sensor Fault Detection
    sanity_res = validate_readings(sorted_readings, cfg)
    all_sensor_faults: list[SensorFaultType] = []
    for flist in sanity_res.faults:
        for f in flist:
            if f not in all_sensor_faults:
                all_sensor_faults.append(f)

    has_sensor_dropout = SensorFaultType.SENSOR_DROPOUT in all_sensor_faults

    # If all readings were invalid / dropped, fallback to estimated extrapolation
    valid_readings = sanity_res.valid_readings
    if not valid_readings:
        # Fallback extrapolation
        current_forecasts = {}
        for stg in all_stages:
            kstate = state.kalman_states[stg.value]
            days_inst = (
                (last_reading.timestamp - state.install_date).total_seconds() / 86400.0
                if state.install_date
                else 30.0
            )
            rl = calculate_remaining_life(kstate, days_inst, cfg)
            current_forecasts[stg] = StageForecast(
                health_percent=round(kstate.health, 2),
                remaining_days=rl.remaining_days,
                band_low=rl.band_low,
                band_high=rl.band_high,
                status_text="Sensor fault; extrapolated forecast",
                estimated=True,
                learning=rl.learning,
            )
        return (
            AnalysisResult(
                stages=current_forecasts,
                active_diagnoses=[],
                event_tags=[],
                is_lite_mode=is_lite_mode,
                device_tier=active_tier,
                sensor_faults_detected=all_sensor_faults,
            ),
            state,
        )

    # 2. Rolling Median Filtering
    filtered_readings = apply_median_filter(valid_readings, cfg)
    effective_latest = filtered_readings[-1]

    # Calculate incremental run hours and water volume
    for i in range(1, len(filtered_readings)):
        prev_r = filtered_readings[i - 1]
        curr_r = filtered_readings[i]
        if curr_r.pump_running:
            dt_sec = max(0.0, (curr_r.timestamp - prev_r.timestamp).total_seconds())
            hours = dt_sec / 3600.0
            state.total_pump_hours += hours
            flow = curr_r.flow_rate if curr_r.flow_rate is not None else 1.2
            state.total_liters_processed += flow * (dt_sec / 60.0)

    # 3. Contextual Event Tagging
    event_tags = tag_reading_events(filtered_readings, cfg)

    # 4. Temperature & Pressure Normalization
    normalized_flow = effective_latest.flow_rate
    if effective_latest.flow_rate is not None and effective_latest.temperature is not None:
        normalized_flow = normalize_flow_temperature(
            effective_latest.flow_rate, effective_latest.temperature, cfg
        )
        if effective_latest.pressure_p3 is not None and effective_latest.pressure_p3 > 0:
            normalized_flow = normalize_flow_feed_pressure(
                normalized_flow, effective_latest.pressure_p3, cfg
            )

    normalized_latest = SensorReading(
        timestamp=effective_latest.timestamp,
        pump_running=effective_latest.pump_running,
        pressure_p1=effective_latest.pressure_p1,
        pressure_p2=effective_latest.pressure_p2,
        pressure_p3=effective_latest.pressure_p3,
        flow_rate=normalized_flow,
        tds_in=effective_latest.tds_in,
        tds_out=effective_latest.tds_out,
        temperature=effective_latest.temperature,
        turbidity=effective_latest.turbidity,
        uv_current=effective_latest.uv_current,
        operating_mode=effective_latest.operating_mode,
        device_tier=active_tier,
    )

    # 5. Baseline State Management
    updated_baseline = compute_baseline(filtered_readings, cfg, existing=state.baseline)
    state.baseline = updated_baseline

    # 6. Stage Health Index Calculation
    health_by_stage: dict[ConsumableType, float] = {}
    is_estimated_by_stage: dict[ConsumableType, bool] = {}

    if not is_lite_mode:
        # FULL Tier: Physics-based telemetry calculations
        stage_hi = compute_stage_health_indices(
            reading=normalized_latest,
            baseline=updated_baseline,
            run_hours=state.total_pump_hours,
            config=cfg,
        )
        health_by_stage = stage_hi.as_dict()
        for stg in all_stages:
            is_estimated_by_stage[stg] = has_sensor_dropout
    else:
        # LITE Mode Fallback: Load-based modeling
        inlet_tds = effective_latest.tds_in or 500.0
        mode = effective_latest.operating_mode or OperatingMode.RO

        # Carbon estimate from load
        carb_est = estimate_carbon_health_from_load(
            cumulative_liters=state.total_liters_processed,
            avg_inlet_tds=inlet_tds,
            mode=mode,
            config=cfg,
        )
        health_by_stage[ConsumableType.CARBON] = carb_est.health_percentage
        health_by_stage[ConsumableType.MEMBRANE_PROTECTOR] = carb_est.health_percentage

        # Sediment from coarse volume consumption (rated 4000 L nominal)
        sed_consumed = state.total_liters_processed / 4000.0
        health_by_stage[ConsumableType.SEDIMENT] = max(
            0.0, min(100.0, 100.0 * (1.0 - sed_consumed))
        )

        # RO membrane from TDS rejection if available, else load-based
        if (
            effective_latest.tds_in is not None
            and effective_latest.tds_out is not None
            and effective_latest.tds_in > 0
        ):
            sp = effective_latest.tds_out / effective_latest.tds_in
            # EOL at salt passage 0.10, new at 0.02
            ro_h = 100.0 * (1.0 - max(0.0, (sp - 0.02) / 0.08))
            health_by_stage[ConsumableType.RO_MEMBRANE] = max(0.0, min(100.0, ro_h))
        else:
            ro_consumed = state.total_liters_processed / 10000.0
            health_by_stage[ConsumableType.RO_MEMBRANE] = max(
                0.0, min(100.0, 100.0 * (1.0 - ro_consumed))
            )

        # UV lamp from run-hours
        uv_h = 100.0 * (1.0 - (state.total_pump_hours / cfg.uv_rated_hours))
        health_by_stage[ConsumableType.UV_LAMP] = max(0.0, min(100.0, uv_h))

        for stg in all_stages:
            is_estimated_by_stage[stg] = True

    # 7. Kalman Filter Prognostics & RUL Forecasting
    # Time step dt in days
    dt_days = 0.1  # nominal step if no timestamp history
    if state.last_processed_timestamp is not None:
        dt_seconds = (last_reading.timestamp - state.last_processed_timestamp).total_seconds()
        dt_days = max(0.001, dt_seconds / 86400.0)

    days_since_install = (
        (last_reading.timestamp - state.install_date).total_seconds() / 86400.0
        if state.install_date
        else 30.0
    )

    stage_forecasts: dict[ConsumableType, StageForecast] = {}
    for stg in all_stages:
        kf = TwoStateKalmanFilter(cfg, initial_state=state.kalman_states[stg.value])
        kf.predict(dt_days)
        measured_health = health_by_stage[stg]
        kf.update(measured_health)
        state.kalman_states[stg.value] = kf.state

        rul = calculate_remaining_life(kf.state, days_since_install=days_since_install, config=cfg)
        mark_estimated = is_estimated_by_stage[stg] or rul.estimated or has_sensor_dropout

        stage_forecasts[stg] = StageForecast(
            health_percent=round(kf.state.health, 2),
            remaining_days=rul.remaining_days,
            band_low=rul.band_low,
            band_high=rul.band_high,
            status_text=rul.status_text,
            estimated=mark_estimated,
            learning=rul.learning,
        )

    # 8. Diagnostic Engine: Rules, Agreement, Event Suppression, and Hysteresis
    active_diagnoses: list[Diagnosis] = []
    if not is_lite_mode:
        sediment_fc = stage_forecasts[ConsumableType.SEDIMENT]
        candidate_rules = evaluate_rules(
            reading=normalized_latest,
            baseline=updated_baseline,
            sediment_remaining_days=sediment_fc.remaining_days,
            sediment_health=sediment_fc.health_percent,
            config=cfg,
        )

        agreed_diagnoses = verify_agreement(
            diagnoses=candidate_rules,
            reading=normalized_latest,
            baseline=updated_baseline,
            sediment_remaining_days=sediment_fc.remaining_days,
            sediment_health=sediment_fc.health_percent,
            config=cfg,
        )

        unsuppressed = filter_suppressed_diagnoses(agreed_diagnoses, event_tags)
        tracker = HysteresisTracker(config=cfg, state=state.hysteresis)
        active_diagnoses = tracker.process(unsuppressed)
        state.hysteresis = tracker.state

    state.last_processed_timestamp = last_reading.timestamp

    result = AnalysisResult(
        stages=stage_forecasts,
        active_diagnoses=active_diagnoses,
        event_tags=event_tags,
        is_lite_mode=is_lite_mode,
        device_tier=active_tier,
        sensor_faults_detected=all_sensor_faults,
    )

    return result, state
