"""CLI script to seed demo tenants, users, households, devices, and cartridges."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
import secrets
import sys

# Ensure src is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import select

from purecast.core.security import hash_password
from purecast.domain.enums import ConsumableType, DeviceTier, OperatingMode, Role
from purecast.infrastructure.db.audit import log_audit
from purecast.infrastructure.db.models import (
    Cartridge,
    CartridgeModel,
    Device,
    DeviceCredential,
    Household,
    Tenant,
    User,
)
from purecast.infrastructure.db.session import async_session_factory, engine


async def seed_demo_data() -> None:
    """Seed 2 tenants, users with varying roles, households, devices, and cartridges."""
    async with async_session_factory() as session:
        print("🌱 Seeding PureCast demonstration database...")

        # ── Tenant 1: Atomberg Technologies ──────────────────────────
        res = await session.execute(select(Tenant).filter(Tenant.slug == "atomberg"))
        t1 = res.scalars().first()
        if not t1:
            t1 = Tenant(
                name="Atomberg Technologies",
                slug="atomberg",
                tier="FULL",
                is_active=True,
            )
            session.add(t1)
            await session.flush()
            print(f"  [+] Created Tenant 1: {t1.name} ({t1.slug})")

        # Users for Tenant 1
        t1_users_data = [
            ("admin@atomberg.com", "Atomberg Admin", Role.TENANT_ADMIN),
            ("analyst@atomberg.com", "Anil Analyst", Role.TENANT_ANALYST),
            ("tech1@atomberg.com", "Ramesh Tech", Role.SERVICE_TECHNICIAN),
            ("customer1@gmail.com", "Priya Sharma", Role.HOUSEHOLD_OWNER),
        ]
        t1_users = {}
        for email, name, role in t1_users_data:
            res = await session.execute(
                select(User).filter(User.tenant_id == t1.id, User.email == email)
            )
            user = res.scalars().first()
            if not user:
                user = User(
                    tenant_id=t1.id,
                    email=email,
                    hashed_password=hash_password("DemoPassword123!"),
                    full_name=name,
                    role=role.value,
                    is_active=True,
                )
                session.add(user)
                await session.flush()
                print(f"    - User: {email} ({role.value})")
            t1_users[email] = user

        # Households for Tenant 1
        res = await session.execute(
            select(Household).filter(Household.tenant_id == t1.id, Household.name == "Sharma Residence")
        )
        h1 = res.scalars().first()
        if not h1:
            h1 = Household(
                tenant_id=t1.id,
                name="Sharma Residence",
                address="Flat 402, Lotus Tower, Powai, Mumbai",
                owner_user_id=t1_users["customer1@gmail.com"].id,
            )
            session.add(h1)
            await session.flush()
            print(f"    - Household: {h1.name}")

        # Cartridge Models for Tenant 1
        cartridge_models = {}
        for ctype in ConsumableType:
            res = await session.execute(
                select(CartridgeModel).filter(
                    CartridgeModel.tenant_id == t1.id,
                    CartridgeModel.consumable_type == ctype.value,
                )
            )
            cmod = res.scalars().first()
            if not cmod:
                cmod = CartridgeModel(
                    tenant_id=t1.id,
                    consumable_type=ctype.value,
                    model_number=f"MOD-{ctype.value[:3]}-2026",
                    rated_capacity_liters=6000.0,
                    rated_lifespan_days=365,
                )
                session.add(cmod)
                await session.flush()
            cartridge_models[ctype.value] = cmod

        # Device 1: FULL Tier
        res = await session.execute(select(Device).filter(Device.serial_number == "ATM-X1-001"))
        d1 = res.scalars().first()
        if not d1:
            d1 = Device(
                tenant_id=t1.id,
                household_id=h1.id,
                serial_number="ATM-X1-001",
                device_tier=DeviceTier.FULL.value,
                model_name="AtomPure-X1 Pro",
                operating_mode=OperatingMode.RO.value,
                is_active=True,
                installed_at=datetime.now(UTC),
            )
            session.add(d1)
            await session.flush()

            # Edge credentials
            cred1 = DeviceCredential(
                tenant_id=t1.id,
                device_id=d1.id,
                client_id="purecast_ATM-X1-001",
                hashed_secret=hash_password(secrets.token_urlsafe(16)),
            )
            session.add(cred1)

            # Cartridges for d1
            for ctype in ConsumableType:
                c = Cartridge(
                    tenant_id=t1.id,
                    device_id=d1.id,
                    model_id=cartridge_models[ctype.value].id,
                    consumable_type=ctype.value,
                    serial_number=f"CRT-{ctype.value[:3]}-1001",
                    installed_at=datetime.now(UTC),
                    current_health_percentage=98.5,
                    remaining_days=350,
                )
                session.add(c)
            print(f"    - Device: {d1.serial_number} ({d1.device_tier}) with all 5 consumables")

        # Device 2: LITE Tier
        res = await session.execute(select(Device).filter(Device.serial_number == "ATM-LT-002"))
        d2 = res.scalars().first()
        if not d2:
            d2 = Device(
                tenant_id=t1.id,
                household_id=h1.id,
                serial_number="ATM-LT-002",
                device_tier=DeviceTier.LITE.value,
                model_name="AtomPure-Lite",
                operating_mode=OperatingMode.RO.value,
                is_active=True,
                installed_at=datetime.now(UTC),
            )
            session.add(d2)
            await session.flush()
            cred2 = DeviceCredential(
                tenant_id=t1.id,
                device_id=d2.id,
                client_id="purecast_ATM-LT-002",
                hashed_secret=hash_password(secrets.token_urlsafe(16)),
            )
            session.add(cred2)
            print(f"    - Device: {d2.serial_number} ({d2.device_tier})")

        # ── Tenant 2: Aquaguard OEM Services ─────────────────────────
        res = await session.execute(select(Tenant).filter(Tenant.slug == "aquaguard"))
        t2 = res.scalars().first()
        if not t2:
            t2 = Tenant(
                name="Aquaguard OEM Services",
                slug="aquaguard",
                tier="FULL",
                is_active=True,
            )
            session.add(t2)
            await session.flush()
            print(f"  [+] Created Tenant 2: {t2.name} ({t2.slug})")

        # Users for Tenant 2
        t2_users_data = [
            ("admin@aquaguard.com", "Aquaguard Admin", Role.TENANT_ADMIN),
            ("tech@aquaguard.com", "Suresh Technician", Role.SERVICE_TECHNICIAN),
        ]
        for email, name, role in t2_users_data:
            res = await session.execute(
                select(User).filter(User.tenant_id == t2.id, User.email == email)
            )
            user = res.scalars().first()
            if not user:
                user = User(
                    tenant_id=t2.id,
                    email=email,
                    hashed_password=hash_password("DemoPassword123!"),
                    full_name=name,
                    role=role.value,
                    is_active=True,
                )
                session.add(user)
                await session.flush()
                print(f"    - User: {email} ({role.value})")

        # Household for Tenant 2
        res = await session.execute(
            select(Household).filter(Household.tenant_id == t2.id, Household.name == "Verma Residence")
        )
        h2 = res.scalars().first()
        if not h2:
            h2 = Household(
                tenant_id=t2.id,
                name="Verma Residence",
                address="Sector 15, Gurgaon, Haryana",
            )
            session.add(h2)
            await session.flush()

        # Device for Tenant 2
        res = await session.execute(select(Device).filter(Device.serial_number == "AQM-PRO-101"))
        d3 = res.scalars().first()
        if not d3:
            d3 = Device(
                tenant_id=t2.id,
                household_id=h2.id,
                serial_number="AQM-PRO-101",
                device_tier=DeviceTier.FULL.value,
                model_name="AquaMax Pro Plus",
                operating_mode=OperatingMode.RO.value,
                is_active=True,
                installed_at=datetime.now(UTC),
            )
            session.add(d3)
            await session.flush()
            cred3 = DeviceCredential(
                tenant_id=t2.id,
                device_id=d3.id,
                client_id="purecast_AQM-PRO-101",
                hashed_secret=hash_password(secrets.token_urlsafe(16)),
            )
            session.add(cred3)
            print(f"    - Device: {d3.serial_number} for Tenant 2")

        await session.commit()
        print("✅ Demo data seeded successfully for 2 tenants!")


def main() -> None:
    """Run seeding routine."""
    asyncio.run(seed_demo_data())


if __name__ == "__main__":
    main()
