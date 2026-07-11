@echo off
title Elite Decision Engine - Shutdown

echo ============================================
echo  Stopping Elite Decision Engine...
echo ============================================
echo.

REM Stop backend
taskkill /FI "WINDOWTITLE eq Elite-Backend" /F >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK]  Backend stopped.
) else (
    echo [..]  Backend was not running.
)

REM Stop frontend
taskkill /FI "WINDOWTITLE eq Elite-Frontend" /F >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK]  Frontend stopped.
) else (
    echo [..]  Frontend was not running.
)

echo.
echo ============================================
echo  All processes stopped.
echo ============================================
echo.

exit /b 0
