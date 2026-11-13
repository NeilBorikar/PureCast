# ── PureCast Makefile ─────────────────────────────────────
# Usage: make <target>
# Supported: install, dev, lint, test, up, down, migrate, seed
# ──────────────────────────────────────────────────────────

.DEFAULT_GOAL := help
PYTHON := python
UV := uv

# ── Environment ──────────────────────────────────────────

.PHONY: install
install: ## Install all dependencies
	$(PYTHON) -m pip install -e . || $(UV) pip install -e .

# ── Development ──────────────────────────────────────────

.PHONY: dev
dev: ## Run the API server with hot-reload
	$(PYTHON) -m uvicorn purecast.main:app --reload --host 0.0.0.0 --port 8000

# ── Quality ──────────────────────────────────────────────

.PHONY: lint
lint: ## Run ruff linter
	$(PYTHON) -m ruff check src/ tests/

.PHONY: lint-fix
lint-fix: ## Auto-fix linting issues
	$(PYTHON) -m ruff check --fix src/ tests/

.PHONY: format
format: ## Format code with ruff
	$(PYTHON) -m ruff format src/ tests/

# ── Testing ──────────────────────────────────────────────

.PHONY: test
test: ## Run unit and integration tests with coverage
	$(PYTHON) -m pytest tests/unit/ tests/integration/ -v --tb=short --cov=src/purecast --cov-report=term-missing

# ── Docker ───────────────────────────────────────────────

.PHONY: up
up: ## Start docker-compose dev stack
	docker compose up -d

.PHONY: down
down: ## Stop docker-compose stack
	docker compose down

# ── Database ─────────────────────────────────────────────

.PHONY: migrate
migrate: ## Run database migrations
	$(PYTHON) -m alembic upgrade head

# ── Seed ─────────────────────────────────────────────────

.PHONY: seed
seed: ## Seed demonstration data
	$(PYTHON) scripts/seed_demo.py

.PHONY: create-admin
create-admin: ## Create platform admin user
	$(PYTHON) scripts/create_admin.py

.PHONY: help
help: ## Show this help message
	@echo "PureCast Phase 1 Targets: install, dev, lint, test, up, down, migrate, seed"
