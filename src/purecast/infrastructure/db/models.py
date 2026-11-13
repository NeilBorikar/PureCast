"""Database models for PureCast multi-tenant architecture.

All tables inherit from Base and include UUID primary keys and UTC timestamps.
Tenant-scoped models include tenant_id with foreign key relationships.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""

    metadata = MetaData(naming_convention=convention)


class TimestampMixin:
    """Mixin providing created_at and updated_at UTC timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class TenantScopedMixin(TimestampMixin):
    """Mixin for multi-tenant isolation, UUID primary key, and timestamps."""

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


# 1. Tenant
class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(50), default="FULL", nullable=False)

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="tenant", cascade="all, delete-orphan"
    )
    devices: Mapped[list["Device"]] = relationship(
        "Device", back_populates="tenant", cascade="all, delete-orphan"
    )


# 2. User
class User(Base, TenantScopedMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="HOUSEHOLD_OWNER", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_users_tenant_email", "tenant_id", "email", unique=True),)


# 3. RefreshToken
class RefreshToken(Base, TenantScopedMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    jti: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


# 4. ApiKey
class ApiKey(Base, TenantScopedMixin):
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="DEVICE", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# 5. Household
class Household(Base, TenantScopedMixin):
    __tablename__ = "households"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    owner_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    devices: Mapped[list["Device"]] = relationship("Device", back_populates="household")


# 6. Device
class Device(Base, TenantScopedMixin):
    __tablename__ = "devices"

    household_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("households.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    device_tier: Mapped[str] = mapped_column(String(50), default="FULL", nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operating_mode: Mapped[str] = mapped_column(String(50), default="RO", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    online_status: Mapped[str] = mapped_column(String(50), default="OFFLINE", nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="devices")
    household: Mapped["Household | None"] = relationship("Household", back_populates="devices")
    credentials: Mapped["DeviceCredential | None"] = relationship(
        "DeviceCredential", back_populates="device", uselist=False, cascade="all, delete-orphan"
    )
    cartridges: Mapped[list["Cartridge"]] = relationship(
        "Cartridge", back_populates="device", cascade="all, delete-orphan"
    )


# 7. DeviceCredential
class DeviceCredential(Base, TenantScopedMixin):
    __tablename__ = "device_credentials"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    client_id: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    secret_key: Mapped[str | None] = mapped_column(String(255), nullable=True)

    device: Mapped["Device"] = relationship("Device", back_populates="credentials")


# 8. CartridgeModel
class CartridgeModel(Base, TenantScopedMixin):
    __tablename__ = "cartridge_models"

    consumable_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model_number: Mapped[str] = mapped_column(String(100), nullable=False)
    rated_capacity_liters: Mapped[float] = mapped_column(Float, default=6000.0, nullable=False)
    rated_lifespan_days: Mapped[int] = mapped_column(Integer, default=365, nullable=False)


# 9. Cartridge
class Cartridge(Base, TenantScopedMixin):
    __tablename__ = "cartridges"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cartridge_models.id", ondelete="SET NULL"), nullable=True
    )
    consumable_type: Mapped[str] = mapped_column(String(50), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_health_percentage: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    remaining_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    device: Mapped["Device"] = relationship("Device", back_populates="cartridges")

    __table_args__ = (
        CheckConstraint(
            "current_health_percentage >= 0 AND current_health_percentage <= 100",
            name="ck_cartridge_health_pct",
        ),
    )


# 10. TelemetryReading (Timescale hypertable, 1-day chunks)
class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, default=lambda: datetime.now(UTC), nullable=False
    )
    device_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    pressure_p1: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_p2: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_p3: Mapped[float | None] = mapped_column(Float, nullable=True)
    flow_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    tds_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    tds_out: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    turbidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    uv_current: Mapped[float | None] = mapped_column(Float, nullable=True)
    pump_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (Index("ix_telemetry_device_time", "device_id", "time"),)


# 11. HealthSnapshot
class HealthSnapshot(Base, TenantScopedMixin):
    __tablename__ = "health_snapshots"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        CheckConstraint("overall_score >= 0 AND overall_score <= 100", name="ck_snapshot_score"),
    )


# 12. Forecast
class Forecast(Base, TenantScopedMixin):
    __tablename__ = "forecasts"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consumable_type: Mapped[str] = mapped_column(String(50), nullable=False)
    predicted_eol_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    remaining_days: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_interval_lower: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_interval_upper: Mapped[int | None] = mapped_column(Integer, nullable=True)
    health_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    learning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


# 13. Diagnosis
class Diagnosis(Base, TenantScopedMixin):
    __tablename__ = "diagnoses"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fault_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 100", name="ck_diagnosis_confidence"),
    )


# 14. Alert
class Alert(Base, TenantScopedMixin):
    __tablename__ = "alerts"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    fault_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# 15. Event
class Event(Base, TenantScopedMixin):
    __tablename__ = "events"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


# 16. Plan
class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False)
    price_monthly: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_devices: Mapped[int] = mapped_column(Integer, default=100, nullable=False)


# 17. Subscription
class Subscription(Base, TenantScopedMixin):
    __tablename__ = "subscriptions"

    plan_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# 18. Order
class Order(Base, TenantScopedMixin):
    __tablename__ = "orders"

    household_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)


# 19. ServiceRequest
class ServiceRequest(Base, TenantScopedMixin):
    __tablename__ = "service_requests"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    technician_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# 20. UsageRecord
class UsageRecord(Base, TenantScopedMixin):
    __tablename__ = "usage_records"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)




# 21. TestRun
class TestRun(Base, TenantScopedMixin):
    __tablename__ = "test_runs"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    results: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

# 22. AuditLog
class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

# 23. DeviceStateRecord
class DeviceStateRecord(Base, TenantScopedMixin):
    __tablename__ = "device_states"

    device_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    state_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

# 24. DeadLetterMessage
class DeadLetterMessage(Base):
    __tablename__ = "dead_letter_messages"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    device_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

# 25. Invoice
class Invoice(Base, TenantScopedMixin):
    __tablename__ = "invoices"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    line_items: Mapped[list["InvoiceLineItem"]] = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")

# 26. InvoiceLineItem
class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    invoice_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    item_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="line_items")

