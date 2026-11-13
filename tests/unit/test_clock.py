"""Unit tests for injectable clock mechanism."""

from datetime import UTC, datetime, timedelta

import pytest

from purecast.core.clock import FrozenClock, SystemClock, get_clock, set_clock


@pytest.mark.unit
def test_system_clock_returns_utc() -> None:
    """Validate SystemClock returns timezone-aware UTC datetime."""
    clock = SystemClock()
    t1 = clock.now()
    assert t1.tzinfo is not None
    assert t1.tzinfo == UTC


@pytest.mark.unit
def test_frozen_clock_deterministic_advancement() -> None:
    """Validate FrozenClock stays fixed until explicitly advanced."""
    fixed_time = datetime(2026, 6, 15, 10, 30, 0, tzinfo=UTC)
    clock = FrozenClock(fixed_time)

    assert clock.now() == fixed_time
    assert clock.now() == fixed_time  # Doesn't drift

    # Advance by 2 hours
    clock.tick(timedelta(hours=2))
    assert clock.now() == datetime(2026, 6, 15, 12, 30, 0, tzinfo=UTC)

    # Set new time directly
    new_time = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
    clock.set_time(new_time)
    assert clock.now() == new_time


@pytest.mark.unit
def test_set_and_get_global_clock() -> None:
    """Validate clock dependency injection."""
    original_clock = get_clock()
    frozen = FrozenClock()
    set_clock(frozen)

    assert get_clock() is frozen
    set_clock(original_clock)
    assert get_clock() is original_clock

