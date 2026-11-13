"""Phase 3 schema additions: device state persistence, dead letter, status and alerts metadata.

Revision ID: 0002_phase3_features
Revises: 0001_initial_schema
Create Date: 2026-11-01 20:50:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_phase3_features"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. devices additions
    op.add_column("devices", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "devices",
        sa.Column("online_status", sa.String(length=50), nullable=False, server_default="OFFLINE"),
    )

    # 2. device_credentials additions
    op.add_column("device_credentials", sa.Column("secret_key", sa.String(length=255), nullable=True))

    # 3. forecasts additions
    op.add_column("forecasts", sa.Column("health_percent", sa.Float(), nullable=True))
    op.add_column(
        "forecasts",
        sa.Column("estimated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "forecasts",
        sa.Column("learning", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # 4. alerts additions
    op.add_column(
        "alerts",
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
    )
    op.add_column("alerts", sa.Column("fault_type", sa.String(length=50), nullable=True))
    op.add_column("alerts", sa.Column("reason_code", sa.String(length=100), nullable=True))

    # 5. device_states table
    op.create_table(
        "device_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"], ["devices.id"], name=op.f("fk_device_states_device_id_devices"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name=op.f("fk_device_states_tenant_id_tenants"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_device_states")),
        sa.UniqueConstraint("device_id", name=op.f("uq_device_states_device_id")),
    )
    op.create_index(op.f("ix_device_states_device_id"), "device_states", ["device_id"], unique=True)
    op.create_index(op.f("ix_device_states_tenant_id"), "device_states", ["tenant_id"])

    # 6. dead_letter_messages table
    op.create_table(
        "dead_letter_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("device_id", sa.Uuid(), nullable=True),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dead_letter_messages")),
    )
    op.create_index(op.f("ix_dead_letter_messages_tenant_id"), "dead_letter_messages", ["tenant_id"])
    op.create_index(op.f("ix_dead_letter_messages_device_id"), "dead_letter_messages", ["device_id"])


def downgrade() -> None:
    op.drop_table("dead_letter_messages")
    op.drop_table("device_states")
    op.drop_column("alerts", "reason_code")
    op.drop_column("alerts", "fault_type")
    op.drop_column("alerts", "status")
    op.drop_column("forecasts", "learning")
    op.drop_column("forecasts", "estimated")
    op.drop_column("forecasts", "health_percent")
    op.drop_column("device_credentials", "secret_key")
    op.drop_column("devices", "online_status")
    op.drop_column("devices", "last_seen_at")

