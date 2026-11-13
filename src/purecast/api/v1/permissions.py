"""Role-based access control (RBAC) permission map and checkers."""

from purecast.domain.enums import Role

ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.PLATFORM_ADMIN: {"*"},
    Role.TENANT_ADMIN: {
        "tenant:read",
        "tenant:update",
        "tenant:api_keys",
        "user:create",
        "user:read",
        "user:update",
        "user:delete",
        "household:create",
        "household:read",
        "household:update",
        "household:delete",
        "device:create",
        "device:read",
        "device:update",
        "device:delete",
        "cartridge:read",
        "cartridge:write",
        "telemetry:read",
        "forecast:read",
        "diagnosis:read",
        "alert:read",
        "alert:ack",
        "order:create",
        "order:read",
        "order:update",
        "service_request:create",
        "service_request:read",
        "service_request:update",
    },
    Role.TENANT_ANALYST: {
        "tenant:read",
        "user:read",
        "household:read",
        "device:read",
        "cartridge:read",
        "telemetry:read",
        "forecast:read",
        "diagnosis:read",
        "alert:read",
    },
    Role.SERVICE_TECHNICIAN: {
        "device:read",
        "device:update",
        "cartridge:read",
        "cartridge:write",
        "telemetry:read",
        "forecast:read",
        "diagnosis:read",
        "alert:read",
        "alert:ack",
        "service_request:read",
        "service_request:update",
    },
    Role.HOUSEHOLD_OWNER: {
        "household:read",
        "household:update",
        "device:read",
        "telemetry:read",
        "forecast:read",
        "alert:read",
        "alert:ack",
        "order:create",
        "order:read",
        "service_request:create",
        "service_request:read",
    },
    Role.DEVICE: {
        "telemetry:write",
        "device:read_config",
    },
}


def has_permission(role: Role | str, permission: str) -> bool:
    """Check if a given role possesses the required permission string."""
    try:
        r = Role(role) if isinstance(role, str) else role
    except ValueError:
        return False

    permissions = ROLE_PERMISSIONS.get(r, set())
    if "*" in permissions:
        return True
    return permission in permissions

