"""Integration test: Alembic migration applies cleanly."""

import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


@pytest.mark.integration
def test_migration_applies_and_creates_all_tables() -> None:
    """Verify Alembic migration script creates all 22 required tables."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_sqlite_file = Path(tmp_dir) / "migration_test.db"
        async_sqlite_url = f"sqlite+aiosqlite:///{test_sqlite_file.as_posix()}"
        sync_sqlite_url = f"sqlite:///{test_sqlite_file.as_posix()}"

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", async_sqlite_url)

        # Run migration to head
        command.upgrade(alembic_cfg, "head")

        # Inspect created tables in database
        engine = create_engine(sync_sqlite_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        expected_tables = {
            "tenants",
            "users",
            "refresh_tokens",
            "api_keys",
            "households",
            "devices",
            "device_credentials",
            "cartridges",
            "cartridge_models",
            "telemetry_readings",
            "health_snapshots",
            "forecasts",
            "diagnoses",
            "alerts",
            "events",
            "orders",
            "service_requests",
            "plans",
            "subscriptions",
            "usage_records",
            "test_runs",
            "audit_logs",
        }

        missing = expected_tables - tables
        assert not missing, f"Migration failed to create tables: {missing}"

        # Verify downgrade drops them cleanly
        command.downgrade(alembic_cfg, "base")
        inspector_after = inspect(engine)
        remaining = set(inspector_after.get_table_names()) - {"alembic_version"}
        assert not remaining, f"Downgrade left tables behind: {remaining}"

        # Dispose engine so SQLite closes the file on Windows
        engine.dispose()
