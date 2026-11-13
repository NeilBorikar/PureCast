"""End-to-end domain scenario tests verifying full pipeline decisions across all fault modes."""

from datetime import datetime, timedelta

from purecast.domain.config import AlgorithmConfig
from purecast.domain.enums import ConsumableType, DeviceTier, EventType, FaultType
from purecast.domain.health.baseline import BaselineState
from purecast.domain.prognostics.kalman import KalmanState
from purecast.domain.reading import SensorReading
from purecast.domain.services.pipeline import DeviceState, analyze


def make_established_state() -> DeviceState:
    """Create a healthy initialized device state with established baseline."""
    baseline = BaselineState(
        flow_rate=1.20,
        salt_passage=0.02,
        prefilter_dp=5.0,
        uv_current=400.0,
        feed_pressure_p3=45.0,
        sample_count=40,
        is_established=True,
    )
    kalman_states = {
        ConsumableType.SEDIMENT.value: KalmanState(health=95.0, rate=-0.25),
        ConsumableType.CARBON.value: KalmanState(health=95.0, rate=-0.20),
        ConsumableType.MEMBRANE_PROTECTOR.value: KalmanState(health=95.0, rate=-0.20),
        ConsumableType.RO_MEMBRANE.value: KalmanState(health=98.0, rate=-0.10),
        ConsumableType.UV_LAMP.value: KalmanState(health=98.0, rate=-0.15),
    }
    return DeviceState(
        kalman_states=kalman_states,
        baseline=baseline,
        install_date=datetime(2026, 10, 1, 0, 0, 0),
        last_processed_timestamp=datetime(2026, 11, 1, 8, 0, 0),
        device_tier=DeviceTier.FULL,
    )


# ── Scenario 1: COLD WATER (T < 18 °C) -> No Alarm ────────────────────────────


def test_scenario_cold_water_morning_suppresses_false_alarms() -> None:
    """Cold feed water (12 °C) causes physical flux drop, but algorithm normalizes and tags COLD_WATER_MORNING without raising alarms."""
    state = make_established_state()
    t0 = datetime(2026, 11, 1, 8, 30, 0)

    # At 12 °C, raw flow drops from 1.20 to ~0.816 due to water viscosity (1 + 0.025*(12-25) = 0.675)
    raw_flow = 1.20 * (1.0 + 0.025 * (12.0 - 25.0))  # 0.81 L/min

    readings = [
        SensorReading(
            timestamp=t0 + timedelta(seconds=i * 10),
            pump_running=True,
            pressure_p1=50.0,
            pressure_p2=45.0,  # dP = 5.0 (normal)
            pressure_p3=45.0,  # feed pressure normal
            flow_rate=raw_flow,
            tds_in=500.0,
            tds_out=10.0,  # salt passage = 0.02 (healthy)
            temperature=12.0,  # cold water
            turbidity=0.5,
            uv_current=400.0,
        )
        for i in range(5)
    ]

    result, updated_state = analyze(state, readings)

    # Invariants:
    # 1. Event tag COLD_WATER_MORNING must be detected
    assert EventType.COLD_WATER_MORNING in result.event_tags

    # 2. No membrane fouling alarm should be raised
    fault_types = [d.fault_type for d in result.active_diagnoses]
    assert FaultType.MEMBRANE_FOULING_SCALING not in fault_types
    assert len(result.active_diagnoses) == 0


# ── Scenario 2: THROTTLED INLET -> SUPPLY_FAULT, NOT a filter fault ───────────


def test_scenario_throttled_inlet_diagnoses_supply_fault() -> None:
    """When inlet feed pressure P3 is severely low while prefilter dP is normal, diagnosis must be SUPPLY_FAULT with text: 'Supply problem, not a filter problem'."""
    state = make_established_state()
    t0 = datetime(2026, 11, 1, 9, 0, 0)

    readings = [
        SensorReading(
            timestamp=t0 + timedelta(seconds=i * 10),
            pump_running=True,
            pressure_p1=15.0,
            pressure_p2=12.0,  # dP = 3.0 psi (completely normal prefilter)
            pressure_p3=8.0,  # P3 is 8 psi (< 15 psi threshold: severely throttled)
            flow_rate=0.40,  # depressed flow due to lack of supply pressure
            tds_in=500.0,
            tds_out=10.0,
            temperature=25.0,
            turbidity=0.5,
            uv_current=400.0,
        )
        for i in range(5)
    ]

    result, updated_state = analyze(state, readings)

    # Must diagnose SUPPLY_FAULT
    fault_types = [d.fault_type for d in result.active_diagnoses]
    assert FaultType.SUPPLY_FAULT in fault_types
    # Must NOT diagnose PREFILTER_CLOG or MEMBRANE_FOULING_SCALING
    assert FaultType.PREFILTER_CLOG not in fault_types
    assert FaultType.MEMBRANE_FOULING_SCALING not in fault_types

    supply_diag = next(d for d in result.active_diagnoses if d.fault_type == FaultType.SUPPLY_FAULT)
    assert "Supply problem, not a filter problem" in supply_diag.human_text


# ── Scenario 3: CLAY SLURRY -> PREFILTER_CLOG & Sediment Forecast Shrinks ──────


def test_scenario_clay_slurry_prefilter_clog() -> None:
    """High sediment/turbidity raises prefilter pressure drop, shrinking remaining days and diagnosing PREFILTER_CLOG."""
    state = make_established_state()
    # Artificially age sediment close to threshold
    state.kalman_states[ConsumableType.SEDIMENT.value] = KalmanState(
        health=75.0, rate=-1.20, p00=0.5, p11=0.01
    )
    t0 = datetime(2026, 11, 1, 10, 0, 0)

    # Baseline prefilter dP is 5.0 psi. Clay causes dP to rise to 8.5 psi (> 12% rise)
    readings = [
        SensorReading(
            timestamp=t0 + timedelta(seconds=i * 10),
            pump_running=True,
            pressure_p1=58.5,
            pressure_p2=50.0,  # dP = 8.5 psi (significant rise)
            pressure_p3=45.0,
            flow_rate=0.95,  # depressed flow
            tds_in=500.0,
            tds_out=10.0,
            temperature=25.0,
            turbidity=15.0,  # high clay turbidity
            uv_current=400.0,
        )
        for i in range(5)
    ]

    result, updated_state = analyze(state, readings)

    fault_types = [d.fault_type for d in result.active_diagnoses]
    assert FaultType.PREFILTER_CLOG in fault_types

    # Sediment forecast remaining days must shrink significantly
    sed_fc = result.stages[ConsumableType.SEDIMENT]
    assert sed_fc.remaining_days is not None
    assert sed_fc.remaining_days < 70
    assert sed_fc.health_percent < 85.0


# ── Scenario 4: MEMBRANE FOULING / SCALING ────────────────────────────────────


def test_scenario_membrane_fouling_scaling() -> None:
    """Permeate flow drops while salt passage remains stable (rejection intact) -> MEMBRANE_FOULING_SCALING."""
    state = make_established_state()
    t0 = datetime(2026, 11, 1, 11, 0, 0)

    # Flow drops to 0.75 L/min at 25 °C while salt passage is unchanged at 0.02
    readings = [
        SensorReading(
            timestamp=t0 + timedelta(seconds=i * 10),
            pump_running=True,
            pressure_p1=50.0,
            pressure_p2=45.0,  # dP = 5.0 (normal)
            pressure_p3=45.0,  # supply pressure healthy
            flow_rate=0.75,  # ~38% drop in permeate flow
            tds_in=500.0,
            tds_out=10.0,  # rejection is rock solid 98%
            temperature=25.0,
            turbidity=0.5,
            uv_current=400.0,
        )
        for i in range(5)
    ]

    result, updated_state = analyze(state, readings)
    fault_types = [d.fault_type for d in result.active_diagnoses]
    assert FaultType.MEMBRANE_FOULING_SCALING in fault_types


# ── Scenario 5: MEMBRANE WEAR / MICRO-BREACH ──────────────────────────────────


def test_scenario_membrane_wear() -> None:
    """Salt passage rises significantly (> 0.06 vs 0.02 baseline) while flow is normal -> MEMBRANE_WEAR."""
    state = make_established_state()
    t0 = datetime(2026, 11, 1, 12, 0, 0)

    readings = [
        SensorReading(
            timestamp=t0 + timedelta(seconds=i * 10),
            pump_running=True,
            pressure_p1=50.0,
            pressure_p2=45.0,
            pressure_p3=45.0,
            flow_rate=1.20,  # flow unblocked
            tds_in=600.0,
            tds_out=80.0,  # salt passage = 80/600 = 0.133 (> baseline 0.02 + 0.04)
            temperature=25.0,
            turbidity=0.5,
            uv_current=400.0,
        )
        for i in range(5)
    ]

    result, updated_state = analyze(state, readings)
    fault_types = [d.fault_type for d in result.active_diagnoses]
    assert FaultType.MEMBRANE_WEAR in fault_types


# ── Scenario 6: UV LAMP WEAKENING ─────────────────────────────────────────────


def test_scenario_uv_lamp_weakening() -> None:
    """UV current drifts by >= 20% (e.g. down to 280 mA from 400 mA) -> UV_LAMP_WEAKENING."""
    state = make_established_state()
    t0 = datetime(2026, 11, 1, 13, 0, 0)

    readings = [
        SensorReading(
            timestamp=t0 + timedelta(seconds=i * 10),
            pump_running=True,
            pressure_p1=50.0,
            pressure_p2=45.0,
            pressure_p3=45.0,
            flow_rate=1.20,
            tds_in=500.0,
            tds_out=10.0,
            temperature=25.0,
            turbidity=0.5,
            uv_current=280.0,  # 30% drift from 400 mA nominal
        )
        for i in range(5)
    ]

    result, updated_state = analyze(state, readings)
    fault_types = [d.fault_type for d in result.active_diagnoses]
    assert FaultType.UV_LAMP_WEAKENING in fault_types


# ── Scenario 7: SENSOR DROPOUT -> estimated=True ──────────────────────────────


def test_scenario_sensor_dropout_sets_estimated_flag() -> None:
    """When essential sensors drop out in FULL tier, the pipeline flags SENSOR_DROPOUT and marks forecasts estimated=True."""
    state = make_established_state()
    t0 = datetime(2026, 11, 1, 14, 0, 0)

    # Missing pressure_p1 in FULL tier
    readings = [
        SensorReading(
            timestamp=t0 + timedelta(seconds=i * 10),
            pump_running=True,
            pressure_p1=None,  # sensor unplugged / broken wire
            pressure_p2=45.0,
            pressure_p3=45.0,
            flow_rate=1.20,
            tds_in=500.0,
            tds_out=10.0,
            temperature=25.0,
            turbidity=0.5,
            uv_current=400.0,
        )
        for i in range(5)
    ]

    result, updated_state = analyze(state, readings)

    # Invariants:
    # 1. SENSOR_DROPOUT detected in sensor_faults
    assert any("SENSOR_DROPOUT" in str(f) for f in result.sensor_faults_detected)

    # 2. Forecasts must be marked estimated=True
    assert result.stages[ConsumableType.SEDIMENT].estimated is True
    assert result.stages[ConsumableType.CARBON].estimated is True
    assert result.stages[ConsumableType.RO_MEMBRANE].estimated is True


# ── Scenario 8: LITE MODE FALLBACK ────────────────────────────────────────────


def test_scenario_lite_mode_fallback() -> None:
    """LITE tier devices (software-only with TDS and pump state, no pressure/turbidity) compute coarse forecast via load model with estimated=True."""
    state = DeviceState(device_tier=DeviceTier.LITE)
    t0 = datetime(2026, 11, 1, 15, 0, 0)

    readings = [
        SensorReading(
            timestamp=t0 + timedelta(seconds=i * 60),
            pump_running=True,
            pressure_p1=None,
            pressure_p2=None,
            pressure_p3=None,
            flow_rate=None,
            tds_in=650.0,
            tds_out=25.0,
            temperature=None,
            turbidity=None,
            uv_current=None,
            device_tier=DeviceTier.LITE,
        )
        for i in range(10)
    ]

    result, updated_state = analyze(state, readings)

    assert result.is_lite_mode is True
    assert result.device_tier == DeviceTier.LITE
    # All stages should be estimated in LITE mode
    for stage_fc in result.stages.values():
        assert stage_fc.estimated is True

