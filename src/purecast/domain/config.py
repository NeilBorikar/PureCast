"""Single frozen configuration dataclass for all domain algorithms."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AlgorithmConfig:
    """Configurable domain algorithm parameters with physics-based defaults."""

    # ── Signal & Sanity Parameters ────────────────────────────
    median_window_seconds: float = 60.0
    frozen_samples_threshold: int = 10
    flow_while_pump_off_threshold: float = 0.05  # L/min
    tds_inversion_tolerance: float = 0.0  # ppm

    # Sensor physical bounds
    min_tds: float = 0.0
    max_tds: float = 3000.0  # ppm
    min_pressure: float = 0.0
    max_pressure: float = 150.0  # psi
    min_flow: float = 0.0
    max_flow: float = 20.0  # L/min
    min_temp_c: float = 1.0
    max_temp_c: float = 60.0  # °C
    min_turbidity: float = 0.0
    max_turbidity: float = 50.0  # NTU
    min_uv_current: float = 0.0
    max_uv_current: float = 1000.0  # mA

    # Temperature & Pressure normalization
    ref_temp_c: float = 25.0
    temp_flow_coeff: float = 0.025  # 2.5% per °C (standard RO membrane viscosity/permeability)
    temp_tds_coeff: float = 0.020  # 2.0% per °C (standard conductivity compensation)
    ref_net_driving_pressure_psi: float = 40.0

    # ── Baselines & EOL Limits ───────────────────────────────
    baseline_sample_count: int = 30
    eol_flow_drop_fraction: float = 0.10  # 10% drop in normalized permeate flow
    eol_salt_passage_rise_fraction: float = 0.08  # 8% rise in salt passage (5-10% range)
    eol_prefilter_dp_rise_fraction: float = 0.12  # 12% rise in prefilter dP (P1-P2)

    # UV Lamp specs
    uv_nominal_current_ma: float = 400.0
    uv_eol_current_drift_fraction: float = 0.20  # 20% drift from nominal
    uv_rated_hours: float = 365.0 * 24.0  # 8760 hours (1 year)

    # Load Model (Carbon & Mode Ageing)
    carbon_rated_liters: float = 6000.0
    carbon_ref_tds: float = 500.0
    carbon_ref_turbidity: float = 1.0
    ageing_multiplier_ro: float = 1.0
    ageing_multiplier_uf_uv: float = 0.7
    ageing_multiplier_vacay: float = 0.1

    # ── Prognostics & Kalman Filter ──────────────────────────
    kalman_q_health: float = 1e-4
    kalman_q_rate: float = 1e-6
    kalman_r_meas: float = 1.0
    kalman_initial_p_health: float = 1.0
    kalman_initial_p_rate: float = 0.01

    safety_margin_fraction: float = 0.10  # 10% early warning bias
    learning_period_days: int = 14
    learning_band_multiplier: float = 2.0

    # Physics nominal days to EOL under nominal load
    nominal_days_sediment: float = 150.0
    nominal_days_carbon: float = 270.0
    nominal_days_protector: float = 270.0
    nominal_days_ro: float = 540.0
    nominal_days_uv: float = 365.0

    # ── Diagnosis & Alerts ───────────────────────────────────
    hysteresis_raise_threshold: float = 0.75
    hysteresis_clear_threshold: float = 0.60
    cold_morning_temp_c: float = 18.0
    holiday_inactivity_days: float = 3.0
    low_supply_pressure_psi: float = 15.0
    prefilter_dp_normal_max_psi: float = 8.0

