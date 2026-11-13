@echo off
rem Simple make runner for Windows CMD / PowerShell

if "%1"=="" goto help
if "%1"=="install" goto install
if "%1"=="dev" goto dev
if "%1"=="lint" goto lint
if "%1"=="test" goto test
if "%1"=="up" goto up
if "%1"=="down" goto down
if "%1"=="migrate" goto migrate
if "%1"=="seed" goto seed
if "%1"=="create-admin" goto create_admin
if "%1"=="frontend" goto frontend
if "%1"=="start" goto start

:help
echo PureCast Phase 1 Targets: install, dev, frontend, start, lint, test, up, down, migrate, seed
goto :eof

:install
python -m pip install -e .
goto :eof

:dev
python -m uvicorn purecast.main:app --app-dir src --reload --host 0.0.0.0 --port 8000
goto :eof

:lint
python -m ruff check src/ tests/
goto :eof

:test
python -m pytest tests/unit/ tests/integration/ -v --tb=short --cov=src/purecast --cov-report=term-missing
goto :eof

:up
docker compose up -d
goto :eof

:down
docker compose down
goto :eof

:migrate
python -m alembic upgrade head
goto :eof

:seed
python scripts/seed_demo.py
goto :eof

:create_admin
python scripts/create_admin.py
goto :eof

:frontend
cd purecast-frontend && npm run dev
goto :eof

:start
start_purecast.bat
goto :eof

