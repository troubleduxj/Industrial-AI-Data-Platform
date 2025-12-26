@echo off
echo ===================================================
echo   Device Monitor V2 - Development Startup Script
echo ===================================================

REM 检查并激活虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo [Info] Activating virtual environment (.venv)...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [Info] Activating virtual environment (venv)...
    call venv\Scripts\activate.bat
) else (
    echo [Info] No virtual environment found. Using system Python.
)

echo.
echo [1/3] Starting Backend API (Port 8001)...
start "Backend API" cmd /k "if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) else if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) & python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001"

echo [2/3] Starting Celery Worker (Background Tasks)...
start "Celery Worker" cmd /k "if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) else if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) & celery -A app.celery_app worker --loglevel=info -P solo -Q celery,ai_training,ai_evaluation"


echo [3/3] Starting Frontend (Port 3001)...
cd web
start "Frontend Web" cmd /k "npm run dev"
cd ..

echo.
echo ===================================================
echo   All services are starting in new windows.
echo   - Backend: http://localhost:8001/docs
echo   - Frontend: http://localhost:3001
echo ===================================================
echo.
pause
