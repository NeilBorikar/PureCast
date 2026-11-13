"""Learning period adjustment for early-life forecasting."""

from purecast.domain.config import AlgorithmConfig
from purecast.domain.prognostics.remaining_life import RemainingLifeForecast


def is_in_learning_period(
    days_since_install: float,
    config: AlgorithmConfig | None = None,
) -> bool:
    """Return True if the cartridge is within the initial 14-day calibration window."""
    cfg = config or AlgorithmConfig()
    return days_since_install <= cfg.learning_period_days


def adjust_forecast_learning_band(
    forecast: RemainingLifeForecast,
    days_since_install: float,
    config: AlgorithmConfig | None = None,
) -> RemainingLifeForecast:
    """Widen confidence intervals if within the initial learning period."""
    cfg = config or AlgorithmConfig()
    if not is_in_learning_period(days_since_install, cfg):
        return forecast

    if forecast.remaining_days is None or forecast.band_low is None or forecast.band_high is None:
        return RemainingLifeForecast(
            remaining_days=forecast.remaining_days,
            band_low=forecast.band_low,
            band_high=forecast.band_high,
            status_text=forecast.status_text,
            estimated=forecast.estimated,
            learning=True,
        )

    center = float(forecast.remaining_days)
    half_width = max(1.0, float(forecast.band_high - forecast.band_low) / 2.0)
    widened_half = half_width * cfg.learning_band_multiplier

    new_low = max(0, round(center - widened_half))
    new_high = max(new_low, round(center + widened_half))

    return RemainingLifeForecast(
        remaining_days=forecast.remaining_days,
        band_low=new_low,
        band_high=new_high,
        status_text=forecast.status_text,
        estimated=forecast.estimated,
        learning=True,
    )
