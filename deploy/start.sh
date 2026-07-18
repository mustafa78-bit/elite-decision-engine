#!/bin/sh
# =====================================================================
# Elite Decision Engine - Production Startup & Orchestration Orchestrator
# =====================================================================
# This script:
#   1. Runs the configuration validator to ensure everything is production-ready.
#   2. On validation success, orchestrates the launch of Docker Compose.

set -e

echo "================================================================="
echo "   Elite Decision Engine - Bootstrapping Production Stack        "
echo "================================================================="

# Run configuration validation
if python3 scripts/validate_config.py; then
    echo "\n[INFO] Configuration validation passed. Commencing container orchestration..."
else
    echo "\n\033[91m[ERROR] Configuration validation failed. Aborting startup.\033[0m"
    exit 1
fi

# Detect whether to use 'docker compose' or 'docker-compose'
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif docker-compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "\033[91m[ERROR] Neither 'docker compose' nor 'docker-compose' was found on this host.\033[0m"
    echo "Please install Docker Compose before executing this script."
    exit 1
fi

echo "[INFO] Using orchestration tool: ${DOCKER_COMPOSE_CMD}"

# Ensure we are in the correct directory relative to the docker-compose file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

# Build/pull containers and run them detached
echo "[INFO] Starting services in detached mode..."
${DOCKER_COMPOSE_CMD} -f docker-compose.prod.yml up -d

echo "\n================================================================="
echo "\033[92m[SUCCESS] Elite Decision Engine stack successfully initiated!\033[0m"
echo "================================================================="
echo "Access points:"
echo "  - Frontend Dashboard: https://app.elite-decision.io (configured in Traefik)"
echo "  - Backend Rest API:   https://api.elite-decision.io"
echo "  - Grafana Monitor:    https://monitor.elite-decision.io"
echo ""
echo "To check system logs:"
echo "  - ${DOCKER_COMPOSE_CMD} -f docker-compose.prod.yml logs -f"
echo "================================================================="
