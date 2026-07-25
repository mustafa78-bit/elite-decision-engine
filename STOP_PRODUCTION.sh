#!/bin/bash

# ==============================================================================
# Elite Decision Engine - Production Shutdown Script (Unix / macOS / Linux)
# ==============================================================================

echo "=========================================================="
echo " Stopping Elite Decision Engine Production Environment..."
echo "=========================================================="

# 1. Stop backend service
echo "Stopping FastAPI/Uvicorn backend..."
if [ -f "logs/backend.pid" ]; then
    PID=$(cat logs/backend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "[OK] Terminated backend PID $PID gracefully."
    else
        echo "[..] Backend PID $PID is not running."
    fi
    rm -f logs/backend.pid
else
    # Fallback to search-and-kill on port 8000
    PID=$(lsof -t -i :8000)
    if [ ! -z "$PID" ]; then
        kill $PID
        echo "[OK] Terminated backend process on port 8000 (PID: $PID)."
    else
        echo "[..] No running backend process found on port 8000."
    fi
fi

# 2. Stop Caddy Reverse Proxy
echo "Stopping Caddy reverse proxy..."
if command -v caddy &> /dev/null; then
    caddy stop 2>/dev/null || true
    # Make sure background caddy process is killed
    pkill -f "caddy run" || true
    echo "[OK] Caddy stopped."
else
    echo "[..] Caddy command not found. Skipping."
fi

# 3. Clean up port 8000 (just in case multiple workers are lingering)
echo "Cleaning up any lingering FastAPI worker processes..."
LingeringPIDs=$(lsof -t -i :8000)
if [ ! -z "$LingeringPIDs" ]; then
    kill -9 $LingeringPIDs 2>/dev/null || true
    echo "[OK] Forced termination of remaining port 8000 workers."
else
    echo "[OK] Port 8000 is clean."
fi

echo "=========================================================="
echo " All services successfully stopped!"
echo "=========================================================="
echo ""
