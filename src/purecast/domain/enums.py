"""Domain enumerations for PureCast.

These enums define the closed vocabulary for consumable types, fault types,
operating modes, device tiers, user roles, alert severities, and related domain concepts.
They live in the domain layer and have zero external dependencies (pure Python).
"""

from enum import StrEnum, unique


@unique
class ConsumableType(StrEnum):
    """Types of consumable filter cartridges in an RO water purifier."""

    SEDIMENT = "SEDIMENT"
    CARBON = "CARBON"
    MEMBRANE_PROTECTOR = "MEMBRANE_PROTECTOR"
    RO_MEMBRANE = "RO_MEMBRANE"
    UV_LAMP = "UV_LAMP"


@unique
class FaultType(StrEnum):
    """Diagnosed fault modes identified by the diagnosis engine."""

    PREFILTER_CLOG = "PREFILTER_CLOG"
    MEMBRANE_FOULING_SCALING = "MEMBRANE_FOULING_SCALING"
    MEMBRANE_WEAR = "MEMBRANE_WEAR"
    SUPPLY_FAULT = "SUPPLY_FAULT"
    UV_LAMP_WEAKENING = "UV_LAMP_WEAKENING"


@unique
class OperatingMode(StrEnum):
    """Purifier operating modes affecting ageing rates."""

    RO = "RO"
    UF_UV = "UF_UV"
    VACAY = "VACAY"


@unique
class DeviceTier(StrEnum):
    """Device capability tiers determining available features.

    LITE: Software-only — TDS in/out, tank-full, no-water states,
          pump run-time, coarse forecast.
    FULL: Adds pressure, flow, temperature, turbidity sensors;
          stage-level diagnosis and precise forecasting.
    """

    LITE = "LITE"
    FULL = "FULL"


@unique
class Role(StrEnum):
    """RBAC roles for authorization."""

    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    TENANT_ANALYST = "TENANT_ANALYST"
    SERVICE_TECHNICIAN = "SERVICE_TECHNICIAN"
    HOUSEHOLD_OWNER = "HOUSEHOLD_OWNER"
    DEVICE = "DEVICE"


@unique
class UserRole(StrEnum):
    """User roles for access control and backwards compatibility."""

    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    TENANT_ANALYST = "TENANT_ANALYST"
    SERVICE_TECHNICIAN = "SERVICE_TECHNICIAN"
    HOUSEHOLD_OWNER = "HOUSEHOLD_OWNER"
    DEVICE = "DEVICE"
    SUPER_ADMIN = "SUPER_ADMIN"
    TECHNICIAN = "TECHNICIAN"
    HOUSEHOLD_USER = "HOUSEHOLD_USER"
    API_KEY = "API_KEY"


@unique
class AlertSeverity(StrEnum):
    """Alert severity levels for prioritization."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@unique
class AlertStatus(StrEnum):
    """Lifecycle states of an alert."""

    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    SNOOZED = "SNOOZED"
    RESOLVED = "RESOLVED"


@unique
class SensorFaultType(StrEnum):
    """Types of sensor faults (distinct from filter faults)."""

    TDS_INVERSION = "TDS_INVERSION"
    FLOW_WHILE_PUMP_OFF = "FLOW_WHILE_PUMP_OFF"
    FROZEN_VALUE = "FROZEN_VALUE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    SENSOR_DROPOUT = "SENSOR_DROPOUT"


@unique
class EventType(StrEnum):
    """External event types used for false-alarm suppression."""

    POWER_CUT = "POWER_CUT"
    HOLIDAY = "HOLIDAY"
    COLD_WATER_MORNING = "COLD_WATER_MORNING"


@unique
class PlanTier(StrEnum):
    """Subscription plan tiers for the SaaS business model."""

    LITE = "LITE"
    FULL = "FULL"
    ENTERPRISE = "ENTERPRISE"


@unique
class OrderStatus(StrEnum):
    """Lifecycle states for cartridge reorder."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


@unique
class ServiceRequestStatus(StrEnum):
    """Lifecycle states for technician service requests."""

    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
