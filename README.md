# PureCast Backend — Phase 1 (Foundation)

> Multi-tenant Python backend forecasting remaining life of water-purifier filters (SEDIMENT, CARBON, MEMBRANE_PROTECTOR, RO_MEMBRANE, UV_LAMP) from sensor telemetry.

## Quickstart

### Prerequisites
- Python 3.12 (or 3.11+)
- Docker & Docker Compose (optional for local mock testing)

### Setup & Installation
```bash
# 1. Environment configuration
cp .env.example .env

# 2. Install dependencies
make install
# or: pip install -e .

# 3. Apply database migrations
make migrate
# or: alembic upgrade head

# 4. Seed demonstration tenants and accounts
make seed
# or: python scripts/seed_demo.py

# 5. Start development API server
make dev
# or: uvicorn purecast.main:app --reload --port 8000
```

### Make Targets
- `make install` — Install package dependencies
- `make dev` — Start FastAPI server with hot reload at http://localhost:8000 (OpenAPI docs at `/docs`)
- `make lint` — Run `ruff check src/ tests/`
- `make test` — Run unit and integration test suite with coverage
- `make up` — Launch Docker stack (`timescaledb`, `redis`, `mosquitto`, `api`)
- `make down` — Stop Docker stack
- `make migrate` — Run Alembic database migrations
- `make seed` — Seed demo tenants, users, households, devices, and cartridges
