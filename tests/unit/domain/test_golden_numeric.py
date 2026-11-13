"""Golden numeric tests verifying mathematical accuracy and convergence of domain algorithms."""

import math

from purecast.domain.config import AlgorithmConfig
from purecast.domain.enums import ConsumableType
from purecast.domain.health.baseline import BaselineState
from purecast.domain.health.eol_lines import EOLLimits
from purecast.domain.health.health_index import compute_stage_health_indices
from purecast.domain.prognostics.kalman import KalmanState, TwoStateKalmanFilter
from purecast.domain.prognostics.remaining_life import calculate_remaining_life
from purecast.domain.reading import SensorReading
from purecast.domain.signal.temperature_correction import (
    normalize_flow_feed_pressure,
    normalize_flow_temperature,
    normalize_tds_temperature,
)


def test_temperature_correction_golden_values() -> None:
    """A 4 °C drop cuts raw flow by ~10%; corrected flow must be within 2% of baseline."""
    config = AlgorithmConfig(ref_temp_c=25.0, temp_flow_coeff=0.025)
    baseline_flow = 1.50  # L/min at 25 °C

    # Viscosity decreases flow by ~10% at 21 °C (4 °C drop)
    temp_drop_4c = 21.0
    expected_viscosity_factor = 1.0 + config.temp_flow_coeff * (temp_drop_4c - config.ref_temp_c)
    assert math.isclose(expected_viscosity_factor, 0.90, rel_tol=1e-5)

    raw_flow_cold = baseline_flow * expected_viscosity_factor  # 1.35 L/min
    corrected_flow = normalize_flow_temperature(raw_flow_cold, temp_drop_4c, config)

    # Corrected flow should recover the true baseline within 2%
    relative_error = abs(corrected_flow - baseline_flow) / baseline_flow
    assert relative_error < 0.02
    assert math.isclose(corrected_flow, baseline_flow, rel_tol=1e-5)

    # TDS temperature compensation at 15 °C (10 °C drop @ 2%/°C -> 20% conductivity depression)
    raw_tds_cold = 400.0
    corrected_tds = normalize_tds_temperature(raw_tds_cold, 15.0, config)
    assert corrected_tds == 400.0 / (1.0 + 0.02 * (15.0 - 25.0))
    assert corrected_tds == 500.0

    # Net driving pressure correction
    p3_low = 30.0  # reference is 40 psi
    corrected_p_flow = normalize_flow_feed_pressure(1.0, p3_low, config)
    assert corrected_p_flow == 1.0 * (40.0 / 30.0)


def test_health_index_endpoints_golden() -> None:
    """Stage Health Index endpoints: exactly 100% when new, 0% at EOL, and clamped [0, 100]."""
    config = AlgorithmConfig()
    eol = EOLLimits.from_config(config)

    baseline = BaselineState(
        flow_rate=1.0,
        salt_passage=0.02,
        prefilter_dp=10.0,
        uv_current=400.0,
        sample_count=30,
        is_established=True,
    )

    from datetime import datetime

    now = datetime(2026, 11, 1, 12, 0, 0)

    # 1. Brand new state
    new_reading = SensorReading(
        timestamp=now,
        pump_running=True,
        pressure_p1=50.0,
        pressure_p2=40.0,  # dP = 10.0 (matches baseline)
        flow_rate=1.0,  # matches baseline
        tds_in=500.0,
        tds_out=10.0,  # salt passage = 10/500 = 0.02 (matches baseline)
        uv_current=400.0,  # matches baseline
    )
    hi_new = compute_stage_health_indices(new_reading, baseline, run_hours=0.0, config=config)
    assert hi_new.sediment == 100.0
    assert hi_new.carbon == 100.0
    assert hi_new.membrane_protector == 100.0
    assert hi_new.ro_membrane == 100.0
    assert hi_new.uv_lamp == 100.0

    # 2. At EOL limits:
    # Sediment & Carbon: prefilter dP rises by exactly 12% (10.0 * 1.12 = 11.20)
    eol_sed_reading = SensorReading(
        timestamp=now,
        pump_running=True,
        pressure_p1=51.20,
        pressure_p2=40.00,  # dP = 11.20
        flow_rate=1.0,
        tds_in=500.0,
        tds_out=10.0,
        uv_current=400.0,
    )
    hi_eol_sed = compute_stage_health_indices(
        eol_sed_reading, baseline, run_hours=0.0, config=config
    )
    assert math.isclose(hi_eol_sed.sediment, 0.0, abs_tol=0.1)

    # RO Membrane by 10% flow drop (from 1.0 to 0.90)
    eol_ro_flow = SensorReading(
        timestamp=now,
        pump_running=True,
        pressure_p1=50.0,
        pressure_p2=40.0,
        flow_rate=1.0 * (1.0 - eol.flow_drop_fraction),  # 0.90 L/min
        tds_in=500.0,
        tds_out=10.0,
        uv_current=400.0,
    )
    hi_eol_ro = compute_stage_health_indices(eol_ro_flow, baseline, run_hours=0.0, config=config)
    assert math.isclose(hi_eol_ro.ro_membrane, 0.0, abs_tol=0.1)

    # RO Membrane by 8% salt passage rise (from 0.02 to 0.10)
    eol_ro_salt = SensorReading(
        timestamp=now,
        pump_running=True,
        pressure_p1=50.0,
        pressure_p2=40.0,
        flow_rate=1.0,
        tds_in=500.0,
        tds_out=50.0,  # salt passage = 50 / 500 = 0.10 (rise of 0.08)
        uv_current=400.0,
    )
    hi_eol_salt = compute_stage_health_indices(eol_ro_salt, baseline, run_hours=0.0, config=config)
    assert math.isclose(hi_eol_salt.ro_membrane, 0.0, abs_tol=0.1)

    # UV Lamp by current drift 20% (from 400 to 320 mA)
    eol_uv_current = SensorReading(
        timestamp=now,
        pump_running=True,
        uv_current=400.0 * (1.0 - eol.uv_current_drift_fraction),  # 320 mA
    )
    hi_eol_uv = compute_stage_health_indices(eol_uv_current, baseline, run_hours=0.0, config=config)
    assert math.isclose(hi_eol_uv.uv_lamp, 0.0, abs_tol=0.1)

    # UV Lamp by run-hours (8760 h = 365 days)
    hi_eol_uv_hrs = compute_stage_health_indices(
        new_reading, baseline, run_hours=eol.uv_max_hours, config=config
    )
    assert math.isclose(hi_eol_uv_hrs.uv_lamp, 0.0, abs_tol=0.1)

    # 3. Beyond EOL clamping test (never negative)
    extreme_reading = SensorReading(
        timestamp=now,
        pump_running=True,
        pressure_p1=80.0,
        pressure_p2=40.0,  # dP = 40 (4x baseline)
        flow_rate=0.2,  # 80% flow drop
        tds_in=500.0,
        tds_out=250.0,  # 50% salt passage
        uv_current=100.0,
    )
    hi_extreme = compute_stage_health_indices(
        extreme_reading, baseline, run_hours=20000.0, config=config
    )
    assert hi_extreme.sediment == 0.0
    assert hi_extreme.carbon == 0.0
    assert hi_extreme.membrane_protector == 0.0
    assert hi_extreme.ro_membrane == 0.0
    assert hi_extreme.uv_lamp == 0.0


def test_kalman_convergence_synthetic_linear_decline() -> None:
    """Kalman filter estimates degradation rate within 10% after 30 samples on linear decline."""
    config = AlgorithmConfig()
    true_rate = -0.50  # -0.5% health loss per day
    dt = 1.0  # 1 day intervals

    # Initial state: starts at 100% with prior rate guess of -0.20
    initial_state = KalmanState(
        health=100.0,
        rate=-0.20,
        p00=1.0,
        p11=0.05,
    )
    kf = TwoStateKalmanFilter(config=config, initial_state=initial_state)

    true_health = 100.0
    for day in range(1, 35):
        true_health += true_rate * dt
        # Predict forward 1 day
        kf.predict(dt)
        # Update with noisy/exact measurement
        kf.update(true_health)

    # After 30+ samples, estimated rate should be within 10% of true rate (-0.50)
    estimated_rate = kf.state.rate
    rate_error_pct = abs(estimated_rate - true_rate) / abs(true_rate)
    assert (
        rate_error_pct < 0.10
    ), f"Expected rate near {true_rate}, got {estimated_rate} (err: {rate_error_pct:.2%})"

    # Verify RUL forecast gives sensible estimate
    forecast = calculate_remaining_life(kf.state, days_since_install=35.0, config=config)
    assert forecast.remaining_days is not None
    # At health ~83%, with rate -0.5% / day, nominal remaining days ~ 166. With 10% safety margin ~ 150 days
    assert 135 <= forecast.remaining_days <= 165
    assert forecast.band_low is not None and forecast.band_high is not None
    assert forecast.band_low <= forecast.remaining_days <= forecast.band_high

