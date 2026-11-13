"""Detailed component unit tests covering edge cases, serialization, and auxiliary algorithms."""

from datetime import datetime, timedelta, timezone

from purecast.domain.config import AlgorithmConfig
from purecast.domain.diagnosis.agreement import get_independent_indicators, verify_agreement
from purecast.domain.diagnosis.event_tagging import filter_suppressed_diagnoses, tag_reading_events
from purecast.domain.diagnosis.hysteresis import HysteresisState, HysteresisTracker
from purecast.domain.diagnosis.rules import Diagnosis, evaluate_rules
from purecast.domain.enums import ConsumableType, DeviceTier, EventType, FaultType, OperatingMode, SensorFaultType
from purecast.domain.health.baseline import BaselineState, compute_baseline
from purecast.domain.health.load_model import estimate_carbon_health_from_load, get_mode_ageing_multiplier
from purecast.domain.prognostics.kalman import KalmanState
from purecast.domain.prognostics.learning_band import adjust_forecast_learning_band, is_in_learning_period
from purecast.domain.prognostics.remaining_life import RemainingLifeForecast, calculate_remaining_life
from purecast.domain.reading import SensorReading
from purecast.domain.services.pipeline import AnalysisResult, DeviceState, StageForecast, analyze
from purecast.domain.signal.sanity_checks import check_reading_sanity, validate_readings
from purecast.domain.signal.temperature_correction import correct_reading


def test_learning_band_adjustment() -> None:
    config = AlgorithmConfig(learning_period_days=14, learning_band_multiplier=2.0)
    assert is_in_learning_period(5.0, config) is True
    assert is_in_learning_period(15.0, config) is False

    # Within learning period: band widens by 2x
    fc = RemainingLifeForecast(
        remaining_days=100,
        band_low=90,
        band_high=110,
        status_text="Operational",
        estimated=False,
        learning=False,
    )
    adjusted = adjust_forecast_learning_band(fc, days_since_install=5.0, config=config)
    assert adjusted.learning is True
    assert adjusted.band_low < 90
    assert adjusted.band_high > 110

    # Outside learning period: unchanged
    unadjusted = adjust_forecast_learning_band(fc, days_since_install=20.0, config=config)
    assert unadjusted.learning is False
    assert unadjusted.band_low == 90

    # Forecast with None values
    none_fc = RemainingLifeForecast(
        remaining_days=None,
        band_low=None,
        band_high=None,
        status_text="not enough trend",
        estimated=True,
    )
    adj_none = adjust_forecast_learning_band(none_fc, days_since_install=5.0, config=config)
    assert adj_none.learning is True


def test_temperature_correct_reading_helper() -> None:
    t0 = datetime(2026, 11, 1, 12, 0, 0)
    raw = SensorReading(
        timestamp=t0,
        pump_running=True,
        pressure_p1=50.0,
        pressure_p2=45.0,
        pressure_p3=40.0,
        flow_rate=1.0,
        tds_in=500.0,
        tds_out=15.0,
        temperature=20.0,
    )
    corrected = correct_reading(raw)
    assert corrected.flow_rate is not None
    assert corrected.tds_in is not None
    assert corrected.tds_out is not None
    assert corrected.flow_rate > 1.0  # normalized from 20 °C to 25 °C


def test_event_tagging_holiday_and_power_cut() -> None:
    t0 = datetime(2026, 11, 1, 0, 0, 0)
    # Holiday detection from inactivity days
    empty_readings = [
        SensorReading(timestamp=t0 + timedelta(days=i), pump_running=False, flow_rate=0.0)
        for i in range(4)
    ]
    events = tag_reading_events(empty_readings, days_inactive=4.0)
    assert EventType.HOLIDAY in events

    # Holiday detection from timestamps span
    events2 = tag_reading_events(empty_readings, days_inactive=0.0)
    assert EventType.HOLIDAY in events2

    # Power cut detection
    power_readings = [
        SensorReading(timestamp=t0, pump_running=True, flow_rate=1.0, uv_current=400.0),
        SensorReading(timestamp=t0 + timedelta(seconds=10), pump_running=False, flow_rate=0.0, uv_current=0.0),
    ]
    p_events = tag_reading_events(power_readings)
    assert EventType.POWER_CUT in p_events

    # Alarm suppression during POWER_CUT
    diag = Diagnosis(
        fault_type=FaultType.PREFILTER_CLOG,
        reason_code="TEST",
        confidence=0.9,
        evidence={},
        human_text="Test",
    )
    suppressed = filter_suppressed_diagnoses([diag], [EventType.POWER_CUT])
    assert len(suppressed) == 0

    # Alarm suppression during HOLIDAY
    suppressed_hol = filter_suppressed_diagnoses([diag], [EventType.HOLIDAY])
    assert len(suppressed_hol) == 0


def test_hysteresis_tracker_transitions() -> None:
    tracker = HysteresisTracker(config=AlgorithmConfig(hysteresis_raise_threshold=0.75, hysteresis_clear_threshold=0.60))
    fault = FaultType.PREFILTER_CLOG

    # 1. Below raise threshold -> remains inactive
    assert tracker.update(fault, 0.70) is False
    assert tracker.is_active(fault) is False

    # 2. Reaches raise threshold -> transitions to active
    assert tracker.update(fault, 0.80) is True
    assert tracker.is_active(fault) is True

    # 3. Drops between raise and clear thresholds -> stays active
    assert tracker.update(fault, 0.65) is True
    assert tracker.is_active(fault) is True

    # 4. Drops below clear threshold -> transitions to inactive
    assert tracker.update(fault, 0.55) is False
    assert tracker.is_active(fault) is False

    # Test serialization
    state_dict = tracker.state.to_dict()
    reconstituted = HysteresisState.from_dict(state_dict)
    assert reconstituted.active_faults == tracker.state.active_faults


def test_load_model_operating_modes() -> None:
    cfg = AlgorithmConfig()
    assert get_mode_ageing_multiplier(OperatingMode.RO, cfg) == 1.0
    assert get_mode_ageing_multiplier(OperatingMode.UF_UV, cfg) == 0.7
    assert get_mode_ageing_multiplier(OperatingMode.VACAY, cfg) == 0.1

    est_vacay = estimate_carbon_health_from_load(
        cumulative_liters=1000.0,
        mode=OperatingMode.VACAY,
        config=cfg,
    )
    assert est_vacay.health_percentage > 95.0


def test_baseline_computation_and_serialization() -> None:
    t0 = datetime(2026, 11, 1, 0, 0, 0)
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
            uv_current=400.0,
        )
        for i in range(35)
    ]
    base = compute_baseline(readings, config=AlgorithmConfig(baseline_sample_count=30))
    assert base.is_established is True
    assert base.flow_rate == 1.20
    assert base.prefilter_dp == 5.0

    d = base.to_dict()
    from_d = BaselineState.from_dict(d)
    assert from_d.is_established is True
    assert from_d.prefilter_dp == 5.0


def test_sanity_checks_all_fault_types() -> None:
    t0 = datetime(2026, 11, 1, 10, 0, 0)
    # Flow while pump off
    r_leak = SensorReading(timestamp=t0, pump_running=False, flow_rate=1.0)
    faults = check_reading_sanity(r_leak)
    assert SensorFaultType.FLOW_WHILE_PUMP_OFF in faults

    # Out of range (high pressure)
    r_high_p = SensorReading(timestamp=t0, pump_running=True, pressure_p1=250.0)
    assert SensorFaultType.OUT_OF_RANGE in check_reading_sanity(r_high_p)

    # Frozen value across 10 samples
    history = [
        SensorReading(timestamp=t0 + timedelta(seconds=i), pump_running=True, flow_rate=1.25)
        for i in range(10)
    ]
    curr_frozen = SensorReading(timestamp=t0 + timedelta(seconds=11), pump_running=True, flow_rate=1.25)
    assert SensorFaultType.FROZEN_VALUE in check_reading_sanity(curr_frozen, history)


def test_remaining_life_edge_cases() -> None:
    cfg = AlgorithmConfig()
    # Zero health -> 0 days remaining
    k_dead = KalmanState(health=0.0, rate=-0.5)
    assert calculate_remaining_life(k_dead, 30.0, cfg).remaining_days == 0

    # Rate >= 0 -> not enough trend
    k_pos = KalmanState(health=90.0, rate=0.1)
    assert calculate_remaining_life(k_pos, 30.0, cfg).remaining_days is None


def test_pipeline_empty_and_serialization() -> None:
    # 1. Pipeline with empty readings
    res, state = analyze(None, [])
    assert len(res.stages) == 5
    assert res.stages[ConsumableType.SEDIMENT].health_percent == 100.0

    # 2. Pipeline state serialization
    d = state.to_dict()
    reconstituted = DeviceState.from_dict(d)
    assert reconstituted.device_tier == state.device_tier

    # 3. StageForecast serialization
    sf = StageForecast(100.0, 150, 130, 170, "Operational", False, False)
    sf_d = sf.to_dict()
    sf_rec = StageForecast.from_dict(sf_d)
    assert sf_rec.remaining_days == 150

    # 4. AnalysisResult serialization
    res_d = res.to_dict()
    assert "stages" in res_d
    assert "active_diagnoses" in res_d

