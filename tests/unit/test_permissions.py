"""Unit tests for RBAC permissions map."""

import pytest

from purecast.api.v1.permissions import ROLE_PERMISSIONS, has_permission
from purecast.domain.enums import Role


@pytest.mark.unit
def test_all_defined_roles_present_in_permissions_map() -> None:
    """Ensure all Role enum members have an entry in the permissions map."""
    for role in Role:
        assert role in ROLE_PERMISSIONS, f"Role {role} missing from ROLE_PERMISSIONS"


@pytest.mark.unit
def test_platform_admin_wildcard_permission() -> None:
    """Validate PLATFORM_ADMIN holds wildcard access to all permissions."""
    assert has_permission(Role.PLATFORM_ADMIN, "tenant:create") is True
    assert has_permission(Role.PLATFORM_ADMIN, "device:delete") is True
    assert has_permission(Role.PLATFORM_ADMIN, "arbitrary:system:action") is True
    assert has_permission("PLATFORM_ADMIN", "anything") is True


@pytest.mark.unit
def test_tenant_admin_permissions() -> None:
    """Validate TENANT_ADMIN permissions boundaries."""
    role = Role.TENANT_ADMIN
    # Permitted actions
    assert has_permission(role, "device:create") is True
    assert has_permission(role, "user:create") is True
    assert has_permission(role, "tenant:api_keys") is True
    assert has_permission(role, "alert:ack") is True

    # Denied platform actions
    assert has_permission(role, "platform:system_config") is False


@pytest.mark.unit
def test_analyst_read_only_permissions() -> None:
    """Validate TENANT_ANALYST read vs write restrictions."""
    role = Role.TENANT_ANALYST
    assert has_permission(role, "telemetry:read") is True
    assert has_permission(role, "forecast:read") is True
    assert has_permission(role, "diagnosis:read") is True

    # Analysts cannot write
    assert has_permission(role, "device:create") is False
    assert has_permission(role, "user:delete") is False


@pytest.mark.unit
def test_technician_permissions() -> None:
    """Validate SERVICE_TECHNICIAN maintenance permissions."""
    role = Role.SERVICE_TECHNICIAN
    assert has_permission(role, "cartridge:write") is True
    assert has_permission(role, "service_request:update") is True
    assert has_permission(role, "device:read") is True

    assert has_permission(role, "user:create") is False
    assert has_permission(role, "tenant:api_keys") is False


@pytest.mark.unit
def test_household_owner_permissions() -> None:
    """Validate HOUSEHOLD_OWNER permissions."""
    role = Role.HOUSEHOLD_OWNER
    assert has_permission(role, "household:read") is True
    assert has_permission(role, "order:create") is True
    assert has_permission(role, "service_request:create") is True

    assert has_permission(role, "device:delete") is False
    assert has_permission(role, "user:create") is False


@pytest.mark.unit
def test_device_role_permissions() -> None:
    """Validate DEVICE role permissions."""
    role = Role.DEVICE
    assert has_permission(role, "telemetry:write") is True
    assert has_permission(role, "device:read_config") is True

    assert has_permission(role, "user:read") is False
    assert has_permission(role, "order:create") is False


@pytest.mark.unit
def test_invalid_role_permission() -> None:
    """Validate that unknown roles fail safely."""
    assert has_permission("NON_EXISTENT_ROLE", "device:read") is False

