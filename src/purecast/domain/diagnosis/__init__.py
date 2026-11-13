"""Diagnosis engine: rules, agreement verification, hysteresis, event tagging."""

from purecast.domain.diagnosis.agreement import get_independent_indicators, verify_agreement
from purecast.domain.diagnosis.event_tagging import filter_suppressed_diagnoses, tag_reading_events
from purecast.domain.diagnosis.hysteresis import HysteresisState, HysteresisTracker
from purecast.domain.diagnosis.rules import Diagnosis, evaluate_rules

__all__ = [
    "Diagnosis",
    "HysteresisState",
    "HysteresisTracker",
    "evaluate_rules",
    "filter_suppressed_diagnoses",
    "get_independent_indicators",
    "tag_reading_events",
    "verify_agreement",
]
