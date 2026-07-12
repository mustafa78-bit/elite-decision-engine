@echo off
setlocal enabledelayedexpansion
title Elite Decision Engine - Startup

echo ============================================
echo  Elite Decision Engine - Founder Alpha Start
echo ============================================
echo.

set ERR=0

echo [1/10] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Python is not installed or not in PATH.
    set ERR=1
    goto :done
)
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VER=%%V
echo [OK]  Python %PYTHON_VER%

echo [2/10] Checking Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Node.js is not installed or not in PATH.
    set ERR=1
    goto :done
)
for /f "tokens=1" %%V in ('node --version') do set NODE_VER=%%V
echo [OK]  Node %NODE_VER%

echo [3/10] Checking npm...
call npm --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FAIL] npm is not installed or not in PATH.
    set ERR=1
    goto :done
)
for /f "delims=" %%V in ('npm --version') do set NPM_VER=%%V
echo [OK]  npm %NPM_VER%

echo [4/10] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo [FAIL] Virtual environment not found.
    set ERR=1
    goto :done
)
echo [OK]  Virtual environment (.venv)

echo [5/10] Checking frontend dependencies...
if not exist "frontend\node_modules\.package-lock.json" (
    echo [FAIL] frontend/node_modules not found or incomplete.
    set ERR=1
    goto :done
)
echo [OK]  Node modules (frontend/node_modules)

echo.

echo [6/10] Starting FastAPI backend...
set JWT_SECRET=dev-secret-for-local-development
set DATABASE_URL=sqlite:///test_elite.db
start "Elite-Backend" cmd /c "title Elite-Backend && .venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

echo [7/10] Waiting for backend to be ready...
set RETRIES=0
:wait_backend
%SystemRoot%\System32\timeout.exe /t 2 /nobreak >nul 2>&1
set HEALTH=
for /f "delims=" %%R in ('%SystemRoot%\System32\curl.exe -s -o nul -w "%%{http_code}" http://localhost:8000/health 2^>nul') do set HEALTH=%%R
if "!HEALTH!"=="200" (
    echo [OK]  Backend is ready.
    goto :backend_ready
)
set /a RETRIES+=1
if !RETRIES! geq 15 (
    echo [FAIL] Backend did not start within 30 seconds.
    set ERR=1
    goto :done
)
echo        Retrying... (!RETRIES!/15)
goto wait_backend
:backend_ready

echo [8/10] Starting Vite frontend...
start "Elite-Frontend" cmd /c "title Elite-Frontend && cd /d %~dp0frontend && npm.cmd run dev"

echo [9/10] Waiting for frontend to be ready...
set FRONTEND_RETRIES=0
:wait_frontend
%SystemRoot%\System32\timeout.exe /t 2 /nobreak >nul 2>&1
set FRONTEND=
for /f "delims=" %%R in ('%SystemRoot%\System32\curl.exe -s -o nul -w "%%{http_code}" http://localhost:5173 2^>nul') do set FRONTEND=%%R
if "!FRONTEND!"=="200" (
    echo [OK]  Frontend is ready.
    goto :frontend_ready
)
set /a FRONTEND_RETRIES+=1
if !FRONTEND_RETRIES! geq 15 (
    echo [WARN] Frontend did not respond within 30 seconds.
    goto :frontend_ready
)
echo        Retrying... (!FRONTEND_RETRIES!/15)
goto wait_frontend
:frontend_ready

echo [10/10] Opening browser...
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
goto :done

:done
if %ERR% neq 0 (
    echo.
    echo ============================================
    echo  Startup failed with errors. See above.
    echo ============================================
    pause
    exit /b 1
)
exit /b 0
