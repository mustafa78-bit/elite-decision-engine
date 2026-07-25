#!/bin/bash
set -e

# ==============================================================================
# Elite Decision Engine - Production Startup Script (Unix / macOS / Linux)
# ==============================================================================

echo "=========================================================="
echo " Starting Elite Decision Engine in PRODUCTION Mode..."
echo "=========================================================="

# 1. Load production environment variables
if [ -f ".env.production" ]; then
    echo "[OK] Found .env.production. Loading variables..."
    export $(grep -v '^#' .env.production | xargs)
else
    echo "[ERROR] .env.production file is missing!"
    echo "Please copy .env.example to .env.production and populate it."
    exit 1
fi

# Ensure critical variables are set
if [ -z "$DATABASE_URL" ]; then
    echo "[ERROR] DATABASE_URL is not defined in .env.production!"
    exit 1
fi

if [ -z "$JWT_SECRET" ]; then
    echo "[ERROR] JWT_SECRET is not defined in .env.production!"
    exit 1
fi

# 2. Check Python environment
echo "Checking Python environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "[WARNING] No virtual environment found (venv or .venv). Running with system Python..."
fi

# 3. Initialize/Migrate PostgreSQL Database Tables
echo "Initializing/Migrating PostgreSQL Database..."
export API_ENV=production
python -c "
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

# 4. Compile and Build Static Frontend Assets
echo "Building Frontend Static Assets..."
# Map backend URL to frontend build environment
# If VITE_API_URL or VITE_WS_URL are not set in shell but exist in config, export them
if [ -z "$VITE_API_URL" ]; then
    # Parse CORS_ORIGINS or extract host
    export VITE_API_URL="https://127.0.0.1"
fi
if [ -z "$VITE_WS_URL" ]; then
    export VITE_WS_URL="wss://127.0.0.1"
fi

npm --prefix frontend install -D typescript
npm --prefix frontend run build
echo "[OK] Frontend build generated under frontend/dist/"

# 5. Start FastAPI Backend under Production Uvicorn Server
echo "Starting production FastAPI application..."
mkdir -p logs

# Kill any existing server on port 8000
kill $(lsof -t -i :8000) 2>/dev/null || true

# Run uvicorn in the background, forwarding logs to logs/stdout.log and logs/stderr.log
nohup uvicorn api.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4 \
    --limit-concurrency 1000 \
    > logs/stdout.log 2> logs/stderr.log &

BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid
echo "[OK] Backend started in background (PID: $BACKEND_PID)."

# 6. Verify backend is responding
echo "Verifying backend is ready..."
RETRIES=0
MAX_RETRIES=15
READY=false

while [ $RETRIES -lt $MAX_RETRIES ]; do
    sleep 2
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health || true)
    if [ "$STATUS_CODE" == "200" ]; then
        READY=true
        break
    fi
    echo "Waiting for backend... ($((RETRIES+1))/$MAX_RETRIES)"
    RETRIES=$((RETRIES+1))
done

if [ "$READY" = true ]; then
    echo "[OK] Backend is healthy and fully operational on http://127.0.0.1:8000"
else
    echo "[ERROR] Backend failed to respond to health checks within 30 seconds."
    echo "Please check logs/stderr.log and logs/engine.log for stack traces."
    exit 1
fi

# 7. Check reverse proxy
if command -v caddy &> /dev/null; then
    echo "Caddy reverse proxy detected. Checking for configuration..."
    if [ -f "Caddyfile" ]; then
        echo "Starting Caddy in the background..."
        # Stop existing caddy on ports 80/443 if running
        sudo caddy stop 2>/dev/null || true
        sudo nohup caddy run --config ./Caddyfile > logs/caddy.log 2>&1 &
        echo "[OK] Caddy reverse proxy started successfully."
    fi
elif command -v nginx &> /dev/null; then
    echo "Nginx detected. Ensure the configuration from nginx.conf is copied to your Nginx sites-enabled directory."
else
    echo "[WARNING] No reverse proxy (Caddy or Nginx) detected in active shell PATH!"
    echo "You must configure Caddy or Nginx manually to serve the frontend from frontend/dist and route /auth, /ws, etc. to port 8000."
fi

echo ""
echo "=========================================================="
echo " Elite Decision Engine is running in PRODUCTION!"
echo ""
echo " Access through reverse proxy (e.g., https://elite.local or https://127.0.0.1)"
echo " Backend direct: http://127.0.0.1:8000"
echo " Backend logs: logs/stdout.log & logs/engine.log"
echo " To stop the environment, run: ./STOP_PRODUCTION.sh"
echo "=========================================================="
echo ""
