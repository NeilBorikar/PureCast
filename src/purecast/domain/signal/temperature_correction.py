"""Physics-based temperature and pressure correction for water purifier telemetry."""

from purecast.domain.config import AlgorithmConfig
from purecast.domain.reading import SensorReading


def normalize_flow_temperature(
    raw_flow: float,
    temperature_c: float,
    config: AlgorithmConfig | None = None,
) -> float:
    """Normalize membrane permeate flow to standard reference temperature (25 °C).

    Formula: normalized_flow = raw_flow / (1 + 0.025 * (T - 25))
    Accounts for water viscosity change with temperature.
    """
    cfg = config or AlgorithmConfig()
    temp_factor = 1.0 + cfg.temp_flow_coeff * (temperature_c - cfg.ref_temp_c)
    temp_factor = max(temp_factor, 0.1)  # Prevent zero-division
    return raw_flow / temp_factor


def normalize_tds_temperature(
    raw_tds: float,
    temperature_c: float,
    config: AlgorithmConfig | None = None,
) -> float:
    """Compensate TDS conductivity to standard reference temperature (25 °C).

    Formula: normalized_tds = raw_tds / (1 + 0.02 * (T - 25))
    """
    cfg = config or AlgorithmConfig()
    temp_factor = 1.0 + cfg.temp_tds_coeff * (temperature_c - cfg.ref_temp_c)
    temp_factor = max(temp_factor, 0.1)
    return raw_tds / temp_factor


def normalize_flow_feed_pressure(
    flow: float,
    feed_pressure_p3: float,
    config: AlgorithmConfig | None = None,
) -> float:
    """Normalize permeate flow by net driving pressure relative to reference pressure.

    Permeate flux is proportional to net driving pressure across the membrane.
    """
    cfg = config or AlgorithmConfig()
    # Ensure non-zero positive driving pressure
    effective_pressure = max(feed_pressure_p3, 5.0)
    return flow * (cfg.ref_net_driving_pressure_psi / effective_pressure)


def correct_reading(
    reading: SensorReading,
    config: AlgorithmConfig | None = None,
) -> SensorReading:
    """Apply temperature and feed pressure corrections to a single reading."""
    cfg = config or AlgorithmConfig()

    corrected_flow = reading.flow_rate
    corrected_tds_in = reading.tds_in
    corrected_tds_out = reading.tds_out

    temp_c = reading.temperature if reading.temperature is not None else cfg.ref_temp_c

    # 1. Temperature compensation on permeate flow
    if corrected_flow is not None:
        corrected_flow = normalize_flow_temperature(corrected_flow, temp_c, cfg)
        # 2. Feed-pressure normalization (if P3 sensor is present)
        if reading.pressure_p3 is not None and reading.pressure_p3 > 0.0:
            corrected_flow = normalize_flow_feed_pressure(
                corrected_flow, reading.pressure_p3, cfg
            )

    # 3. Temperature compensation on TDS
    if corrected_tds_in is not None:
        corrected_tds_in = normalize_tds_temperature(corrected_tds_in, temp_c, cfg)
    if corrected_tds_out is not None:
        corrected_tds_out = normalize_tds_temperature(corrected_tds_out, temp_c, cfg)

    return SensorReading(
        timestamp=reading.timestamp,
        pump_running=reading.pump_running,
        pressure_p1=reading.pressure_p1,
        pressure_p2=reading.pressure_p2,
        pressure_p3=reading.pressure_p3,
        flow_rate=corrected_flow,
        tds_in=corrected_tds_in,
        tds_out=corrected_tds_out,
        temperature=reading.temperature,
        turbidity=reading.turbidity,
        uv_current=reading.uv_current,
        operating_mode=reading.operating_mode,
        device_tier=reading.device_tier,
    )

