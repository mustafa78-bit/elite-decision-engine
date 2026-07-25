@echo off
title Elite Decision Engine - Production Shutdown

echo ==========================================================
echo  Stopping Elite Decision Engine Production Environment (Windows)...
echo ==========================================================
echo.

:: 1. Stop backend service running on port 8000
echo Stopping FastAPI/Uvicorn backend...
set FOUND=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
    if %ERRORLEVEL% equ 0 set FOUND=1
)

if %FOUND% equ 1 (
    echo [OK] Backend stopped successfully.
) else (
    echo [..] No running backend processes found on port 8000.
)

:: 2. Stop Uvicorn named window if any
taskkill /FI "WINDOWTITLE eq Elite-Production-Backend*" /F >nul 2>&1

:: 3. Stop Caddy Reverse Proxy
echo Stopping Caddy reverse proxy...
taskkill /F /IM caddy.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Caddy reverse proxy stopped.
) else (
    echo [..] Caddy was not running.
)

:: 4. Stop Caddy named window if any
taskkill /FI "WINDOWTITLE eq Elite-Production-Caddy*" /F >nul 2>&1

echo.
echo ==========================================================
echo  All services successfully stopped!
echo ==========================================================
echo.

exit /b 0
