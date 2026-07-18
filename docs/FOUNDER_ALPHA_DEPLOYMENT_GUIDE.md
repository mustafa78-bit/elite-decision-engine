# Elite Decision Engine - Founder Alpha Deployment Guide
=========================================================

Welcome to the **Founder Alpha Deployment Guide** for the **Elite Decision Engine**, an automated paper trading engine and intelligence platform for cryptocurrency markets (Hyperliquid).

This guide details the complete blueprint to orchestrate a secure, containerized, and high-reliability deployment on a fresh server (e.g. Ubuntu 22.04 LTS / 24.04 LTS).

---

## 1. Architecture & Port Mapping

The Elite Decision Engine is structured as a containerized microservices suite managed by **Docker Compose** and fronted by **Traefik v3** as a reverse proxy, SSL/TLS terminator, and router.

```
                      ┌──────────────────────────────────────┐
                      │              INTERNET                │
                      │       (HTTP: 80 / HTTPS: 443)        │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                 ┌────────────────────────────────────────────────┐
                 │                   TRAEFIK v3                   │
                 │              (Reverse Proxy / SSL)             │
                 └──────┬─────────────────┬────────────────┬──────┘
                        │                 │                │
     (app.elite-decision.io)   (api.elite-decision.io)  (monitor.elite-decision.io)
                        │                 │                │
                        ▼                 ▼                ▼
             ┌──────────┴──────────┐   ┌──┴──────────┐  ┌──┴──────────┐
             │      DASHBOARD      │   │     API     │  │   GRAFANA   │
             │   (Nginx / Static)  │   │  (FastAPI)  │  │  (Port 3000)│
             └─────────────────────┘   └──────┬──────┘  └──────┬──────┘
                                              │                │
                                      ┌───────┼────────┐       │
                                      │       │        │       │
                                      ▼       ▼        ▼       ▼
                                   ┌──┴─┐  ┌──┴──┐  ┌──┴─┐  ┌──┴──┐
                                   │ DB │  │REDIS│  │PROM│  │ BKP │
                                   └────┘  └─────┘  └────┘  └─────┘
```

### Port Assignments

The suite strictly isolates backend ports within the Docker internal network (`elite_default`), exposing only ports **80** and **443** publicly via Traefik.

| Service | Container Port | External Host Routing | Purpose |
|---------|----------------|-----------------------|---------|
| `traefik` | `80`, `443` | `:80`, `:443` (Public) | Entrypoint, routing, Let's Encrypt SSL management |
| `db` | `5432` | Internal Only | PostgreSQL 16 database |
| `redis` | `6379` | Internal Only | Redis 7 cache and rate limit database |
| `api` | `8000` | Internal Only | FastAPI web server, WebSocket manager |
| `dashboard` | `80` | Internal Only | Nginx serving React 19 / Vite production build |
| `prometheus`| `9090` | Internal Only | Prometheus v2.53 scraper |
| `grafana` | `3000` | Routed via Traefik | System monitoring dashboard |
| `backup` | - | None (Worker) | Daily crond backup worker |

---

## 2. Server Prerequisites & Setup

Before proceeding, secure a Linux server (minimum 2 vCPU, 4GB RAM recommended) and configure your DNS records:

### A. DNS Setup
Point three `A` records to your server's public IP:
- `app.elite-decision.io` (Frontend Dashboard)
- `api.elite-decision.io` (Backend REST API)
- `monitor.elite-decision.io` (Grafana Monitoring)

*Note: Replace `elite-decision.io` in configurations with your actual target domain.*

### B. Fresh Server Dependency Installation
Update the host system and install the required container runtime:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker compose version
docker --version
```

---

## 3. Configuration & Secrets Management

Configurations are fully centralized within a `.env` file in the repository root. Create this file from `.env.example`:

```bash
cp .env.example .env
```

### Required Production Variables

Ensure the following variables are strictly customised in your `.env` file for production stability:

```env
# ── Server Environment ──
API_ENV=production
DEBUG=false
CORS_ORIGINS=https://app.elite-decision.io

# ── Secrets (REQUIRED) ──
# Minimum 32-character secure secret tokens (DO NOT use defaults)
JWT_SECRET=your_long_random_secure_jwt_string_at_least_32_chars
ENCRYPTION_KEY=your_secure_encryption_key_for_db_fields

# ── Databases ──
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=decision_engine
POSTGRES_USER=postgres
DB_PASSWORD=your_highly_secure_database_password_here
REDIS_PASSWORD=your_highly_secure_redis_password_here

# ── Monitoring & Administration ──
GRAFANA_PASSWORD=your_secure_grafana_admin_password

# ── Offsite Backups (Optional S3 Hook) ──
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET=your-production-db-backups-bucket
```

---

## 4. Production Configuration Validation

To guarantee the environment is fully compliant and free of deployment-blocking misconfigurations, execute the automated verification suite before starting the containers:

```bash
# Run the validation tool
python3 scripts/validate_config.py
```

This tool validates:
- **Phase 1: Environment & Secrets Validation** — Checks security flags, JWT secret length (minimum 32 characters), and CORS security rules (blocks insecure `*` settings).
- **Phase 2: Database Connectivity Check** — Confirms network connectivity and query performance.
- **Phase 3: Filesystem & Permissions Validation** — Confirms write and read permissions on necessary backup and logs volumes.

---

## 5. Deployment with `deploy/start.sh`

Deploying the complete suite is simplified into a single, automated wrapper:

```bash
./deploy/start.sh
```

This orchestration script:
1. Runs `scripts/validate_config.py` to ensure complete system safety.
2. Identifies the local Docker Compose command version.
3. Automatically triggers container builds, volume bindings, network isolation, and launches the entire stack in detached background mode.

Once started, confirm running services:
```bash
docker compose -f docker-compose.prod.yml ps
```

---

## 6. Monitoring & Observability

### A. Accessing the Dashboard
- **Dashboard API Health Check**: Visit `https://api.elite-decision.io/health` to confirm overall status.
- **System Metrics**: Grafana is accessible at `https://monitor.elite-decision.io`.
  - **Username**: `admin`
  - **Password**: The value configured in `GRAFANA_PASSWORD` (defaults to `admin` if not changed).

### B. Custom Dashboard Provisioning
The system comes pre-provisioned with the **Elite Decision Engine Production Overview** dashboard (configured automatically from `monitoring/grafana-dashboards/dashboard.json`).
This tracks:
1. **API Status** — Direct heartbeat from Prometheus scraping the `/metrics` endpoint.
2. **Database Connectivity Status** — Heartbeat verifying PostgreSQL container health.
3. **CPU & Memory Load** — Resource utilisation of the backend engine container.
4. **HTTP Request Latency** — Tracking average request processing time to maintain milliseconds-level speeds.

---

## 7. Automated Database Backups

Reliable state management is backed up by `scripts/backup.sh` scheduled automatically via the container's internal cron service (configured in `docker-compose.prod.yml` to trigger daily at **03:00 AM UTC**).

### Local Backup Rotation
Backups are archived inside the mounted `./backups` host folder. The backup worker runs an automated rotation policy, maintaining a rolling **7-day local retention window** (older archives are pruned automatically to preserve host disk space).

### Offsite Replication
If AWS credentials and `S3_BUCKET` are set in `.env`, the script gracefully uploads compressed database dumps to your secure S3 Bucket under the `/db_backups/` prefix.

### Manual Backup Execution
Run a manual database dump at any time:
```bash
docker compose -f docker-compose.prod.yml exec backup /scripts/backup.sh
```

---

## 8. Logs Inspection & Troubleshooting

Centralized rotating file handlers partition the system events within the mounted `./logs` directory:

| Log File | Logged Modules | Purge Policy |
|----------|----------------|--------------|
| `logs/engine.log` | Core loop, Database connections, App lifecycle | 10 MB limit, 5 backup cycles |
| `logs/trade.log` | Execution pipeline, scoring events, indicators | 10 MB limit, 5 backup cycles |
| `logs/error.log` | Centralized repository of all ERROR & CRITICAL levels | 10 MB limit, 5 backup cycles |

### Standard Troubleshooting Commands

- **Check logs of all containers in real-time**:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f
  ```
- **Inspect backend API logs only**:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f api
  ```
- **Reboot database container**:
  ```bash
  docker compose -f docker-compose.prod.yml restart db
  ```
- **Re-initialize database tables manually**:
  ```bash
  docker compose -f docker-compose.prod.yml exec api python -m database
  ```

---

*This guide prepared specifically for Founder Alpha deployment validation and high-reliability production standards.*
