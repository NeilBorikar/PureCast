@echo off
echo =======================================================
echo          PureCast Telemetry Platform Startup
echo =======================================================
echo.
echo [1/2] Launching PureCast FastAPI Backend (:8000)...
start "PureCast Backend API" cmd /k "python -m uvicorn purecast.main:app --app-dir src --reload --port 8000"

echo [2/2] Launching PureCast Light Sky-Blue Frontend (:5173)...
start "PureCast Frontend" cmd /k "cd purecast-frontend && npm run dev"

echo.
echo PureCast is ready for your 3-minute video recording!
echo Dashboard UI: http://localhost:5173
echo Backend API Docs: http://localhost:8000/docs
echo =======================================================
