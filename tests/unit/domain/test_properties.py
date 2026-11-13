"""Hypothesis property-based tests verifying domain invariants."""

from datetime import datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from purecast.domain.config import AlgorithmConfig
from purecast.domain.enums import SensorFaultType
from purecast.domain.health.baseline import BaselineState
from purecast.domain.health.health_index import compute_stage_health_indices
from purecast.domain.reading import SensorReading
from purecast.domain.signal.median_filter import apply_median_filter
from purecast.domain.signal.sanity_checks import check_reading_sanity, validate_readings


@given(
    tds_in=st.floats(min_value=0.0, max_value=2000.0),
    tds_out_excess=st.floats(min_value=0.01, max_value=500.0),
)
def test_property_sanity_never_allows_tds_inversion(tds_in: float, tds_out_excess: float) -> None:
    """Invariant: When TDS_out > TDS_in, sanity check MUST flag TDS_INVERSION and drop the reading."""
    tds_out = tds_in + tds_out_excess
    reading = SensorReading(
        timestamp=datetime(2026, 11, 1, 10, 0, 0),
        pump_running=True,
        tds_in=tds_in,
        tds_out=tds_out,
    )
    faults = check_reading_sanity(reading)
    assert SensorFaultType.TDS_INVERSION in faults

    # validate_readings must drop it
    result = validate_readings([reading])
    assert len(result.valid_readings) == 0


@given(
    dp=st.floats(min_value=-50.0, max_value=200.0),
    flow=st.floats(min_value=-10.0, max_value=50.0),
    tds_in=st.floats(min_value=1.0, max_value=3000.0),
    tds_out=st.floats(min_value=0.0, max_value=1000.0),
    uv_curr=st.floats(min_value=-100.0, max_value=1500.0),
    run_hours=st.floats(min_value=-100.0, max_value=50000.0),
)
def test_property_health_index_strictly_clamped_0_to_100(
    dp: float,
    flow: float,
    tds_in: float,
    tds_out: float,
    uv_curr: float,
    run_hours: float,
) -> None:
    """Invariant: Stage Health Index values must always be strictly within [0.0, 100.0]."""
    baseline = BaselineState(
        flow_rate=1.2,
        salt_passage=0.02,
        prefilter_dp=8.0,
        uv_current=400.0,
        is_established=True,
    )
    reading = SensorReading(
        timestamp=datetime(2026, 11, 1, 10, 0, 0),
        pump_running=True,
        pressure_p1=dp + 30.0,
        pressure_p2=30.0,
        flow_rate=flow,
        tds_in=tds_in,
        tds_out=tds_out,
        uv_current=uv_curr,
    )

    indices = compute_stage_health_indices(reading, baseline, run_hours=run_hours)

    for stage_val in (
        indices.sediment,
        indices.carbon,
        indices.membrane_protector,
        indices.ro_membrane,
        indices.uv_lamp,
    ):
        assert 0.0 <= stage_val <= 100.0, f"Health index out of bounds: {stage_val}"


@given(
    flow_rates=st.lists(
        st.floats(min_value=0.0, max_value=15.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=20,
    )
)
def test_property_median_filter_stays_within_input_bounds(flow_rates: list[float]) -> None:
    """Invariant: Median-filtered flow rate output must always stay within [min(inputs), max(inputs)]."""
    t0 = datetime(2026, 11, 1, 10, 0, 0)
    config = AlgorithmConfig(median_window_seconds=120.0)

    readings = [
        SensorReading(
            timestamp=t0 + timedelta(seconds=i * 5),
            pump_running=True,
            flow_rate=f,
        )
        for i, f in enumerate(flow_rates)
    ]

    filtered = apply_median_filter(readings, config)
    assert len(filtered) == len(readings)

    min_in = min(flow_rates)
    max_in = max(flow_rates)

    for r in filtered:
        assert r.flow_rate is not None
        assert min_in <= r.flow_rate <= max_in, (
            f"Median output {r.flow_rate} outside [{min_in}, {max_in}]"
        )

