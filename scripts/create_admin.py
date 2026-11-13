"""CLI script to provision a platform admin user in the PureCast database."""

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure src is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import select

from purecast.core.security import hash_password
from purecast.domain.enums import Role
from purecast.infrastructure.db.audit import log_audit
from purecast.infrastructure.db.models import Tenant, User
from purecast.infrastructure.db.session import async_session_factory, engine


async def create_platform_admin(
    email: str, password: str, full_name: str, tenant_name: str, tenant_slug: str
) -> None:
    """Create platform administrator account and root platform tenant in the database."""
    async with async_session_factory() as session:
        # Check or create platform tenant
        res = await session.execute(select(Tenant).filter(Tenant.slug == tenant_slug))
        tenant = res.scalars().first()
        if not tenant:
            tenant = Tenant(
                name=tenant_name,
                slug=tenant_slug,
                tier="ENTERPRISE",
                is_active=True,
            )
            session.add(tenant)
            await session.flush()
            print(f"[OK] Created platform tenant '{tenant_name}' ({tenant.id})")

        # Check or create user
        res = await session.execute(select(User).filter(User.email == email))
        user = res.scalars().first()
        if user:
            print(f"[INFO] User with email '{email}' already exists. Updating role to PLATFORM_ADMIN.")
            user.role = Role.PLATFORM_ADMIN.value
            user.hashed_password = hash_password(password)
            user.is_active = True
        else:
            user = User(
                tenant_id=tenant.id,
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                role=Role.PLATFORM_ADMIN.value,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            print(f"[OK] Created platform admin user '{email}' ({user.id})")

        await log_audit(
            session=session,
            action="admin:create",
            resource_type="user",
            tenant_id=tenant.id,
            user_id=user.id,
            resource_id=str(user.id),
            details={"email": email, "role": Role.PLATFORM_ADMIN.value},
        )
        await session.commit()
        print(f"Platform admin provisioned successfully: {email}")


def main() -> None:
    """Parse CLI arguments for platform admin provisioning."""
    parser = argparse.ArgumentParser(description="Create PureCast Platform Admin")
    parser.add_argument("--email", default="admin@purecast.io", help="Admin email address")
    parser.add_argument("--password", default="purecast_admin_2026", help="Admin password")
    parser.add_argument("--name", default="Platform SuperAdmin", help="Admin full name")
    parser.add_argument("--tenant", default="PureCast Global", help="Tenant organization name")
    parser.add_argument("--slug", default="platform", help="Tenant organization slug")
    args = parser.parse_args()

    asyncio.run(
        create_platform_admin(
            email=args.email,
            password=args.password,
            full_name=args.name,
            tenant_name=args.tenant,
            tenant_slug=args.slug,
        )
    )


if __name__ == "__main__":
    main()
