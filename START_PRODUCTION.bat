@echo off
setlocal enabledelayedexpansion
title Elite Decision Engine - Production Startup

echo ==========================================================
echo  Starting Elite Decision Engine in PRODUCTION Mode (Windows)...
echo ==========================================================
echo.

set ERR=0

:: 1. Load production environment variables
if not exist ".env.production" (
    echo [ERROR] .env.production file is missing!
    echo Please copy .env.example to .env.production and populate it.
    set ERR=1
    goto :done
)

echo [OK] Found .env.production. Loading variables...
for /f "usebackq delims=" %%x in (".env.production") do (
    set "line=%%x"
    if not "!line:~0,1!"=="#" (
        set "%%x"
    )
)

:: Ensure critical variables are set
if "%DATABASE_URL%"=="" (
    echo [ERROR] DATABASE_URL is not defined in .env.production!
    set ERR=1
    goto :done
)

if "%JWT_SECRET%"=="" (
    echo [ERROR] JWT_SECRET is not defined in .env.production!
    set ERR=1
    goto :done
)

:: 2. Check Python Environment
echo Checking Python environment...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    set ERR=1
    goto :done
)

:: Check virtual environment
if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXEC=venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXEC=.venv\Scripts\python.exe"
) else (
    echo [WARNING] Virtual environment not found (venv or .venv). Running with system Python...
    set "PYTHON_EXEC=python"
)

:: 3. Initialize/Migrate PostgreSQL Database
echo Initializing/Migrating PostgreSQL Database...
set API_ENV=production
"%PYTHON_EXEC%" -c "
import sys
import logging
logging.basicConfig(level=logging.INFO)
try:
    import database
    print('Connecting to database and creating tables if missing...')
    database.create_tables()
    print('[OK] Database initialization successful!')
except Exception as e:
    print(f'[ERROR] Failed to initialize database: {e}')
    sys.exit(1)
"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to initialize PostgreSQL tables! Check database connection details in .env.production.
    set ERR=1
    goto :done
)

:: 4. Build Frontend static assets
echo Building Frontend Static Assets...
if "%VITE_API_URL%"=="" set VITE_API_URL=https://127.0.0.1
if "%VITE_WS_URL%"=="" set VITE_WS_URL=wss://127.0.0.1

call npm --prefix frontend install -D typescript
call npm --prefix frontend run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to compile and build production frontend assets!
    set ERR=1
    goto :done
)
echo [OK] Frontend static assets compiled under frontend\dist\

:: 5. Create logs directory
if not exist "logs" mkdir logs

:: 6. Terminate any existing server on port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 7. Start FastAPI Backend under Production Uvicorn Server in background
echo Starting production FastAPI backend...
start "Elite-Production-Backend" /MIN "%PYTHON_EXEC%" -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 4 --limit-concurrency 1000

:: 8. Wait and check health
echo Waiting for backend to be ready...
set RETRIES=0
:wait_backend
%SystemRoot%\System32\timeout.exe /t 2 /nobreak >nul 2>&1
set HEALTH=
for /f "delims=" %%R in ('%SystemRoot%\System32\curl.exe -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/health 2^>nul') do set HEALTH=%%R
if "!HEALTH!"=="200" (
    echo [OK] Backend is healthy and responding.
    goto :backend_ready
)
set /a RETRIES+=1
if !RETRIES! geq 15 (
    echo [ERROR] Backend failed to respond to health checks within 30 seconds.
    echo Please check the uvicorn logs or engine.log.
    set ERR=1
    goto :done
)
echo        Waiting... (!RETRIES!/15)
goto wait_backend
:backend_ready

:: 9. Check Reverse Proxy
where caddy >nul 2>&1
if %ERRORLEVEL% equ 0 (
    if exist "Caddyfile" (
        echo Caddy detected. Starting Caddy reverse proxy...
        start "Elite-Production-Caddy" /MIN caddy run --config .\Caddyfile
        echo [OK] Caddy reverse proxy started successfully.
    )
) else (
    echo [WARNING] Caddy was not found in active PATH.
    echo Please configure Caddy or Nginx manually to serve frontend\dist on port 443/80 and reverse-proxy APIs to port 8000.
)

echo.
echo ==========================================================
echo  Elite Decision Engine is running in PRODUCTION!
echo.
echo  Access through reverse proxy (e.g. https://127.0.0.1 or https://elite.local)
echo  Backend direct: http://127.0.0.1:8000
echo.
echo  To stop the environment, run: STOP_PRODUCTION.bat
echo ==========================================================
echo.
goto :done

:done
if %ERR% neq 0 (
    echo.
    echo ==========================================================
    echo  Startup FAILED with errors! Check configuration.
    echo ==========================================================
    pause
    exit /b 1
)
exit /b 0
