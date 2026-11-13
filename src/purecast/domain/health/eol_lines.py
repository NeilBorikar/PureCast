"""End-of-life (EOL) definition boundaries for purifier consumables."""

from dataclasses import dataclass

from purecast.domain.config import AlgorithmConfig


@dataclass(frozen=True)
class EOLLimits:
    """End-of-life relative change thresholds defining 0% Health Index."""

    flow_drop_fraction: float = 0.10  # 10% drop in normalized permeate flow
    salt_passage_rise: float = 0.08  # 8% absolute rise in salt passage (TDS_out / TDS_in)
    prefilter_dp_rise_fraction: float = 0.12  # 12% rise in prefilter dP (P1 - P2)
    uv_current_drift_fraction: float = 0.20  # 20% drift in UV lamp current
    uv_max_hours: float = 8760.0  # 365 days * 24 hours

    @classmethod
    def from_config(cls, config: AlgorithmConfig) -> "EOLLimits":
        return cls(
            flow_drop_fraction=config.eol_flow_drop_fraction,
            salt_passage_rise=config.eol_salt_passage_rise_fraction,
            prefilter_dp_rise_fraction=config.eol_prefilter_dp_rise_fraction,
            uv_current_drift_fraction=config.uv_eol_current_drift_fraction,
            uv_max_hours=config.uv_rated_hours,
        )

