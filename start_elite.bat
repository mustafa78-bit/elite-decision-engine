@echo off
setlocal enabledelayedexpansion
title Elite Decision Engine - Startup

echo ============================================
echo  Elite Decision Engine — Founder Alpha Start
echo ============================================
echo.

REM ── Prerequisites ──────────────────────────────────────────────────────────

:check_python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Python is not installed or not in PATH.
    echo        Install Python 3.12+ from https://www.python.org/
    pause
    exit /b 1
)
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VER=%%V
echo [OK]  Python %PYTHON_VER%

:check_node
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Node.js is not installed or not in PATH.
    echo        Install Node.js 22+ from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1" %%V in ('node --version') do set NODE_VER=%%V
echo [OK]  Node %NODE_VER%

:check_npm
npm --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FAIL] npm is not installed or not in PATH.
    pause
    exit /b 1
)
for /f %%V in ('npm --version') do set NPM_VER=%%V
echo [OK]  npm %NPM_VER%

:check_venv
if not exist ".venv\Scripts\activate" (
    echo [FAIL] Virtual environment not found.
    echo        Run: python -m venv .venv
    echo        Then: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK]  Virtual environment (.venv)

:check_node_modules
if not exist "frontend\node_modules" (
    echo [FAIL] frontend/node_modules not found.
    echo        Run: cd frontend ^&^& npm install
    pause
    exit /b 1
)
echo [OK]  Node modules (frontend/node_modules)

echo.

REM ── Environment ────────────────────────────────────────────────────────────
set JWT_SECRET=dev-secret-for-local-development
set DATABASE_URL=sqlite:///test_elite.db

REM ── Step 1: Start Backend ──────────────────────────────────────────────────
echo [1/4] Starting FastAPI backend...
start "Elite-Backend" cmd /c "title Elite-Backend && .venv\Scripts\activate && set JWT_SECRET=%JWT_SECRET% && set DATABASE_URL=%DATABASE_URL% && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

REM ── Step 2: Wait for Backend Health Check ──────────────────────────────────
echo [2/4] Waiting for backend to be ready...
set RETRIES=0

:wait_loop
timeout /t 2 /nobreak >nul

REM Capture health check response
for /f "delims=" %%R in ('curl -s http://localhost:8000/health 2^>nul') do set HEALTH_RESPONSE=%%R

if defined HEALTH_RESPONSE (
    echo [OK]  Backend is ready.
    goto :backend_ready
)

set /a RETRIES+=1
if !RETRIES! geq 15 (
    echo [FAIL] Backend did not start within 30 seconds.
    echo.
    echo        Possible issues:
    echo        - Port 8000 already in use
    echo        - Missing Python dependencies (run: .venv\Scripts\pip install -r requirements.txt)
    echo        - Database configuration error
    echo        - Syntax error in Python code
    echo.
    echo        Check the "Elite-Backend" window for error details.
    echo        Press any key to open the backend log, or close this window.
    pause >nul
    start notepad engine.log 2>nul
    exit /b 1
)
echo       Retrying... (!RETRIES!/15)
goto wait_loop

:backend_ready

REM ── Step 3: Start Frontend ─────────────────────────────────────────────────
echo [3/4] Starting Vite frontend...
start "Elite-Frontend" cmd /c "title Elite-Frontend && cd /d %~dp0frontend && npm run dev"

REM ── Step 4: Open Browser ──────────────────────────────────────────────────
echo [4/4] Opening browser...
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo.
echo ============================================
echo  Elite Decision Engine is running!
echo.
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo.
echo  Database: SQLite (test_elite.db)
echo  Auth:     JWT dev secret (login via UI)
echo.
echo  To stop, close windows or run: stop_elite.bat
echo ============================================
echo.

exit /b 0
