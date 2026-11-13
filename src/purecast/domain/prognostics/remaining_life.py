"""Remaining useful life (RUL) forecasting with safety margins and confidence intervals."""

import math
from dataclasses import dataclass

from purecast.domain.config import AlgorithmConfig
from purecast.domain.prognostics.kalman import KalmanState


@dataclass(frozen=True)
class RemainingLifeForecast:
    """Forecast of remaining consumable life."""

    remaining_days: int | None
    band_low: int | None
    band_high: int | None
    status_text: str
    estimated: bool
    learning: bool = False


def calculate_remaining_life(
    kalman_state: KalmanState,
    days_since_install: float = 30.0,
    config: AlgorithmConfig | None = None,
) -> RemainingLifeForecast:
    """Estimate remaining days to EOL with early-bias safety margin and confidence band."""
    cfg = config or AlgorithmConfig()
    health = max(0.0, kalman_state.health)
    rate = kalman_state.rate

    # If health is already 0, remaining days is 0
    if health <= 0.0:
        return RemainingLifeForecast(
            remaining_days=0,
            band_low=0,
            band_high=0,
            status_text="End of life reached",
            estimated=False,
            learning=False,
        )

    # If rate >= 0, there is no decline observed yet
    if rate >= 0.0:
        return RemainingLifeForecast(
            remaining_days=None,
            band_low=None,
            band_high=None,
            status_text="not enough trend",
            estimated=True,
            learning=days_since_install <= cfg.learning_period_days,
        )

    decline_rate = abs(rate)
    nominal_days = health / decline_rate

    # Apply early-bias safety margin (subtract 10% by default)
    safe_days = nominal_days * (1.0 - cfg.safety_margin_fraction)

    # Uncertainty from Kalman covariance (P00 on health, P11 on rate)
    sigma_h = math.sqrt(max(1e-9, kalman_state.p00))
    sigma_r = math.sqrt(max(1e-9, kalman_state.p11))
    rel_unc = math.sqrt((sigma_h / max(health, 1.0)) ** 2 + (sigma_r / decline_rate) ** 2)
    sigma_days = safe_days * rel_unc

    # Check learning phase (first 14 days)
    is_learning = days_since_install <= cfg.learning_period_days
    band_mult = cfg.learning_band_multiplier if is_learning else 1.0
    band_spread = max(2.0, sigma_days * 1.96 * band_mult)

    b_low = max(0, round(safe_days - band_spread))
    b_high = max(b_low, round(safe_days + band_spread))
    est_days = max(0, round(safe_days))

    return RemainingLifeForecast(
        remaining_days=est_days,
        band_low=b_low,
        band_high=b_high,
        status_text="Degrading nominally",
        estimated=False,
        learning=is_learning,
    )
