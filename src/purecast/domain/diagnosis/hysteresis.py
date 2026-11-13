"""Stateful hysteresis tracker to prevent alert flapping.

Applies a dual-threshold band:
- Fault is RAISED only when diagnostic confidence >= raise_threshold (default 0.75).
- Fault remains active until diagnostic confidence falls < clear_threshold (default 0.60).
"""

from dataclasses import dataclass, field

from purecast.domain.config import AlgorithmConfig
from purecast.domain.diagnosis.rules import Diagnosis
from purecast.domain.enums import FaultType


@dataclass
class HysteresisState:
    """Persistent state of active fault alerts across analysis cycles."""

    active_faults: dict[str, bool] = field(default_factory=dict)
    fault_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "active_faults": dict(self.active_faults),
            "fault_scores": dict(self.fault_scores),
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> "HysteresisState":
        active = d.get("active_faults", {})
        scores = d.get("fault_scores", {})
        active_dict = (
            {str(k): bool(v) for k, v in active.items()} if isinstance(active, dict) else {}
        )
        scores_dict = (
            {str(k): float(v) for k, v in scores.items()} if isinstance(scores, dict) else {}
        )
        return cls(
            active_faults=active_dict,
            fault_scores=scores_dict,
        )


class HysteresisTracker:
    """Stateful hysteresis engine maintaining raised/cleared alert state."""

    def __init__(
        self,
        config: AlgorithmConfig | None = None,
        state: HysteresisState | None = None,
    ) -> None:
        cfg = config or AlgorithmConfig()
        self.raise_threshold = cfg.hysteresis_raise_threshold
        self.clear_threshold = cfg.hysteresis_clear_threshold
        self.state = state or HysteresisState()

    def update(self, fault_type: FaultType | str, score: float) -> bool:
        """Update fault status with latest score using dual-threshold hysteresis.

        Returns True if the fault is currently active (raised), False if cleared.
        """
        key = fault_type.value if isinstance(fault_type, FaultType) else str(fault_type)
        is_active = self.state.active_faults.get(key, False)

        if is_active:
            # Stays active until confidence drops below clear_threshold
            if score < self.clear_threshold:
                is_active = False
        # Becomes active only when confidence reaches or exceeds raise_threshold
        elif score >= self.raise_threshold:
            is_active = True

        self.state.active_faults[key] = is_active
        self.state.fault_scores[key] = round(score, 3)
        return is_active

    def is_active(self, fault_type: FaultType | str) -> bool:
        """Check if a fault is currently raised."""
        key = fault_type.value if isinstance(fault_type, FaultType) else str(fault_type)
        return self.state.active_faults.get(key, False)

    def process(self, candidate_diagnoses: list[Diagnosis]) -> list[Diagnosis]:
        """Apply hysteresis to candidate diagnoses and return all currently active alerts."""
        seen_faults: set[str] = set()
        active_diagnoses: list[Diagnosis] = []

        for diag in candidate_diagnoses:
            key = diag.fault_type.value
            seen_faults.add(key)
            if self.update(diag.fault_type, diag.confidence):
                active_diagnoses.append(diag)

        # For faults that were previously active but not observed in candidate diagnoses,
        # update their score to 0.0 (clearing them)
        previously_active = [k for k, v in self.state.active_faults.items() if v]
        for past_fault in previously_active:
            if past_fault not in seen_faults:
                self.update(past_fault, 0.0)

        return active_diagnoses
