"""Initialize SQLite database with schema and demo seed data."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from purecast.core.config import get_settings
from purecast.core.security import hash_password
from purecast.domain.enums import ConsumableType, DeviceTier, OperatingMode, Role
from purecast.infrastructure.db.models import (
    Base,
    Cartridge,
    CartridgeModel,
    Device,
    DeviceCredential,
    Household,
    Tenant,
    User,
    TelemetryReading,
)
from purecast.infrastructure.db.session import create_engine_and_session
from sqlalchemy import select


async def init_and_seed() -> None:
    settings = get_settings()
    db_path = Path(__file__).resolve().parent.parent / "purecast.db"
    db_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    print(f"Connecting to database at {db_url}...")

    engine, session_factory = create_engine_and_session(db_url)

    async with engine.begin() as conn:
        print("Creating all database tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

    async with session_factory() as session:
        print("Seeding demo tenants and accounts...")
        # Check if already seeded
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
            print("  Created Tenant: Atomberg Technologies")

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
            t1_users[email] = user

        # Household for Tenant 1
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

        # Cartridge Models
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

            cred1 = DeviceCredential(
                tenant_id=t1.id,
                device_id=d1.id,
                client_id="purecast_ATM-X1-001",
                hashed_secret=hash_password("device_secret_x1"),
                secret_key="device_secret_x1",
            )
            session.add(cred1)

            health_map = {
                ConsumableType.SEDIMENT.value: (78.4, 68),
                ConsumableType.CARBON.value: (84.2, 112),
                ConsumableType.MEMBRANE_PROTECTOR.value: (91.0, 195),
                ConsumableType.RO_MEMBRANE.value: (93.5, 310),
                ConsumableType.UV_LAMP.value: (88.0, 180),
            }

            for ctype in ConsumableType:
                h_pct, rem_d = health_map.get(ctype.value, (95.0, 300))
                c = Cartridge(
                    tenant_id=t1.id,
                    device_id=d1.id,
                    model_id=cartridge_models[ctype.value].id,
                    consumable_type=ctype.value,
                    serial_number=f"CRT-{ctype.value[:3]}-1001",
                    installed_at=datetime.now(UTC),
                    current_health_percentage=h_pct,
                    remaining_days=rem_d,
                )
                session.add(c)
            print(f"  Created Device: {d1.serial_number} with cartridges")

        # Device 2: LITE Tier
        res = await session.execute(select(Device).filter(Device.serial_number == "ATM-LT-002"))
        d2 = res.scalars().first()
        if not d2:
            d2 = Device(
                tenant_id=t1.id,
                household_id=h1.id,
                serial_number="ATM-LT-002",
                device_tier=DeviceTier.LITE.value,
                model_name="AtomPure-Lite Smart",
                operating_mode=OperatingMode.RO.value,
                is_active=True,
                installed_at=datetime.now(UTC),
            )
            session.add(d2)
            await session.flush()
            print(f"  Created Device: {d2.serial_number}")

        # Seed mock telemetry readings for d1
        res = await session.execute(select(TelemetryReading).filter(TelemetryReading.device_id == d1.id).limit(1))
        if not res.scalars().first():
            print("  Seeding sample telemetry readings...")
            from datetime import timedelta
            now = datetime.now(UTC)
            for i in range(24):
                ts = now - timedelta(hours=24 - i)
                reading = TelemetryReading(
                    time=ts,
                    device_id=d1.id,
                    tenant_id=t1.id,
                    pump_status=1 if i % 2 == 0 else 0,
                    pressure_p1=2.8 + (i % 3) * 0.1,
                    pressure_p2=2.1 + (i % 2) * 0.05,
                    pressure_p3=0.3,
                    flow_rate=1.8 if i % 2 == 0 else 0.0,
                    tds_in=680 + (i % 5) * 12,
                    tds_out=42 + (i % 3) * 2,
                    temperature=26.5 + (i % 4) * 0.4,
                    turbidity=0.4 + (i % 3) * 0.1,
                    uv_current=420.0,
                )
                session.add(reading)

        # Tenant 2: Aquaguard OEM
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

            u2 = User(
                tenant_id=t2.id,
                email="admin@aquaguard.com",
                hashed_password=hash_password("DemoPassword123!"),
                full_name="Aquaguard Admin",
                role=Role.TENANT_ADMIN.value,
                is_active=True,
            )
            session.add(u2)
            await session.flush()

            h2 = Household(
                tenant_id=t2.id,
                name="Verma Residence",
                address="Sector 15, Gurgaon, Haryana",
            )
            session.add(h2)
            await session.flush()

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
            print("  Created Tenant 2: Aquaguard & Device AQM-PRO-101")

        await session.commit()
        print("Database initialized and demo data successfully seeded!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_and_seed())

