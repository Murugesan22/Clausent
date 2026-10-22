@echo off
setlocal enabledelayedexpansion
title CLAUSENT Launcher

cd /d "%~dp0"

echo ========================================================
echo               CLAUSENT SYSTEM LAUNCHER                  
echo ========================================================
echo.

:: 1. Verify Prerequisites
if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found in backend\.venv
    echo Please set up the backend virtual environment first.
    pause
    exit /b 1
)

if not exist "node_modules\" (
    echo [ERROR] Frontend node_modules not found.
    echo Running npm install...
    call npm install
)

:: 1.5 Check PostgreSQL Service
powershell -NoProfile -Command "if (Get-Service -Name '*postgres*' -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' }) { Write-Host '[INFO] PostgreSQL service is active.' -ForegroundColor Green } else { Write-Host '[INFO] PostgreSQL service not detected; system will use resilient SQLite fallback.' -ForegroundColor Yellow }"

:: 2. Check if ports are already in use
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":8000 .*LISTENING"') do (
    echo [WARNING] Port 8000 is already in use by PID %%a.
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":5173 .*LISTENING"') do (
    echo [WARNING] Port 5173 is already in use by PID %%a.
)

echo [1/3] Starting Backend (FastAPI on http://127.0.0.1:8000)...
start "CLAUSENT-Backend" cmd /k "title CLAUSENT-Backend && cd /d "%~dp0backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Starting Frontend (React + Vite on http://localhost:5173)...
start "CLAUSENT-Frontend" cmd /k "title CLAUSENT-Frontend && cd /d "%~dp0" && npm run dev"

echo [3/3] Waiting for services to initialize...
powershell -NoProfile -Command "Start-Sleep -Seconds 3"

echo Opening browser...
start http://localhost:5173

echo.
echo ========================================================
echo   CLAUSENT is running!
echo   ----------------------------------------------------
echo   Frontend Web App : http://localhost:5173
echo   Backend API      : http://127.0.0.1:8000
echo   API Docs (Swagger): http://127.0.0.1:8000/docs
echo ========================================================
echo.
echo You can keep this window open or close it.
echo To STOP all services, run stop.bat or press any key below.
echo.
pause

call "%~dp0stop.bat"
