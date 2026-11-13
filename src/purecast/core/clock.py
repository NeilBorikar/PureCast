"""Injectable clock for deterministic time in tests and domain logic."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta


class Clock(ABC):
    """Abstract clock interface."""

    @abstractmethod
    def now(self) -> datetime:
        """Return the current timezone-aware UTC datetime."""
        ...


class SystemClock(Clock):
    """Real system clock returning current UTC datetime."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock(Clock):
    """Deterministic clock for testing and simulation."""

    def __init__(self, current_time: datetime | None = None) -> None:
        if current_time is None:
            self._current_time = datetime.now(UTC)
        elif current_time.tzinfo is None:
            self._current_time = current_time.replace(tzinfo=UTC)
        else:
            self._current_time = current_time

    def now(self) -> datetime:
        return self._current_time

    def set_time(self, new_time: datetime) -> None:
        if new_time.tzinfo is None:
            self._current_time = new_time.replace(tzinfo=UTC)
        else:
            self._current_time = new_time

    def tick(self, delta: timedelta) -> datetime:
        self._current_time += delta
        return self._current_time


_global_clock: Clock = SystemClock()


def get_clock() -> Clock:
    """Get the active clock instance."""
    return _global_clock


def set_clock(clock: Clock) -> None:
    """Set the active clock instance (useful in tests)."""
    global _global_clock  # noqa: PLW0603
    _global_clock = clock
