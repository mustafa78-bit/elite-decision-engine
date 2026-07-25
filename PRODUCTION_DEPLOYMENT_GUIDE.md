# Production Deployment Guide — Self-Hosted Workstation

This guide explains how to deploy, secure, and maintain the **Elite Decision Engine** as a production-grade application running directly on a self-hosted computer (macOS, Linux, or Windows) without relying on localhost development tooling (`npm run dev` or uvicorn hot-reloads).

By following this guide, a founder can access the application securely over HTTPS (with compression and optimal security headers) directly via a local domain (e.g., `https://elite.local` or `https://127.0.0.1`) served by a dedicated production-grade reverse proxy.

---

## Architecture Overview

In a self-hosted production setup, the application components are partitioned as follows:

```
┌────────────────────────────────────────────────────────┐
│                   Founder's Browser                    │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS (Port 443)
                           ▼
┌────────────────────────────────────────────────────────┐
│           Reverse Proxy (Caddy or Nginx)               │
│  Serves Static Frontend Assets directly (from dist/)   │
│  Terminates SSL/TLS & enforces HTTP Security Headers    │
└──────────────┬───────────────────────────┬─────────────┘
               │ proxy requests            │ proxy WebSockets
               ▼                           ▼
┌──────────────────────────────┐ ┌───────────────────────┐
│     FastAPI Backend (8000)   │ │  WebSockets (ws/...)  │
│  Running in production mode  │ │  Real-time data feeds │
└──────────────┬───────────────┘ └───────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│  PostgreSQL Database (5432)  │
│  Persistent storage volume   │
└──────────────────────────────┘
```

---

## 1. System Requirements

- **Python**: Version `3.12` or `3.13`
- **Node.js**: Version `20` or higher (only needed to build production assets)
- **Database**: PostgreSQL (v15 or higher) running natively or in a container
- **Reverse Proxy**: Caddy (recommended for ease of use and auto-HTTPS) or Nginx

---

## 2. Production Environment Variables (`.env.production`)

Create a `.env.production` file in the root directory. This contains sensitive secrets and environment-specific parameters.

```bash
# Core Environment Settings
API_ENV=production
LOG_LEVEL=info
DEBUG=false

# Authentication Security (Minimum 32 bytes high-entropy secret)
# Generate via: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=4f9b88ad39cf5c772be55a5b9e07f918e959635b7cc6d9df262a0a2569faee98
ENCRYPTION_KEY=a7d2e9b884fbc90d1f1e1a5b82810a4e76c12d93e80f76a5c1d9f8e7d2c3b4a5

# PostgreSQL Database Connection
# Replace with your actual credentials and host
DATABASE_URL=postgresql://elite_admin:SecureAdminPassword123!@localhost:5432/elite_production

# CORS Configurations (Specify your custom domain/IP)
CORS_ORIGINS=https://elite.local,https://127.0.0.1
CORS_ORIGIN_REGEX=^https://(elite\.local|127\.0\.0\.1)(:\d+)?$

# Operational Limits
CHECK_INTERVAL=10
MIN_SCORE=85
MAX_OPEN_TRADES=3
MAX_EXPOSURE_PER_SYMBOL=200000
MAX_PORTFOLIO_EXPOSURE=500000
MAX_DAILY_LOSS=10000
MAX_POSITION_SIZE_USD=100000
ACCOUNT_EQUITY=10000
RISK_PER_TRADE_PERCENT=1.0
ATR_MULTIPLIER=1.5
MIN_POSITION_QUANTITY=0.001
```

---

## 3. PostgreSQL Database Setup

Production requires **PostgreSQL** for robustness, data integrity, and safety.

### Option A: Native Installation

1. **Install PostgreSQL**:
   - **macOS**: `brew install postgresql@16`
   - **Ubuntu/Debian**: `sudo apt install postgresql postgresql-contrib`
   - **Windows**: Download and run the installer from the [official PostgreSQL website](https://www.postgresql.org/download/windows/).

2. **Configure Database & User**:
   Connect via `psql` (or pgAdmin) and execute:
   ```sql
   -- Create production database
   CREATE DATABASE elite_production;

   -- Create administration user
   CREATE USER elite_admin WITH PASSWORD 'SecureAdminPassword123!';

   -- Grant permissions
   GRANT ALL PRIVILEGES ON DATABASE elite_production TO elite_admin;
   ```

### Option B: Docker Container (Easy Configuration)

If you prefer running PostgreSQL inside a container:
```bash
docker run -d \
  --name elite-postgres \
  --restart unless-stopped \
  -e POSTGRES_DB=elite_production \
  -e POSTGRES_USER=elite_admin \
  -e POSTGRES_PASSWORD=SecureAdminPassword123! \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16-alpine
```

---

## 4. Frontend Production Build

The production frontend is a set of static HTML, CSS, and JS files. It must be built locally to support super-fast routing and sub-millisecond response times.

1. Install dependencies:
   ```bash
   npm --prefix frontend install
   ```
2. Compile and bundle static files:
   ```bash
   npm --prefix frontend run build
   ```
This generates all optimized production static assets under the `frontend/dist/` directory.

---

## 5. Reverse Proxy Configurations (HTTPS, Static Files, APIs, & WebSockets)

A reverse proxy serves the frontend static assets directly, handles SSL termination (HTTPS), and forwards API/WebSocket requests to the background FastAPI server.

Select **Caddy** (highly recommended for local trust certificates) or **Nginx**.

### Option A: Caddy Configuration (`Caddyfile`)

Caddy is the simplest and most robust choice for self-hosting. It automatically generates and trusts local TLS certificates (meaning no security warnings on `https://localhost` or `https://elite.local`!).

Create a file named `Caddyfile` in your repository root:

```caddy
# Local custom domain (can also use 'localhost' or '127.0.0.1')
elite.local, 127.0.0.1 {
    # Enable gzip and zstd compression
    encode gzip zstd

    # Root directory of compiled frontend assets
    root * ./frontend/dist
    file_server

    # Fallback to SPA router (React Router) for unmatched routes
    try_files {path} /index.html

    # Proxy backend API endpoints
    # All REST endpoints are proxied to the uvicorn application
    reverse_proxy /auth/* 127.0.0.1:8000
    reverse_proxy /health 127.0.0.1:8000
    reverse_proxy /health/details 127.0.0.1:8000
    reverse_proxy /monitoring 127.0.0.1:8000
    reverse_proxy /notifications* 127.0.0.1:8000
    reverse_proxy /signals* 127.0.0.1:8000
    reverse_proxy /risk* 127.0.0.1:8000
    reverse_proxy /portfolio* 127.0.0.1:8000
    reverse_proxy /position-sizing* 127.0.0.1:8000
    reverse_proxy /performance* 127.0.0.1:8000
    reverse_proxy /backtest* 127.0.0.1:8000
    reverse_proxy /intelligence* 127.0.0.1:8000
    reverse_proxy /trading-control* 127.0.0.1:8000
    reverse_proxy /market* 127.0.0.1:8000
    reverse_proxy /regime 127.0.0.1:8000
    reverse_proxy /users* 127.0.0.1:8000
    reverse_proxy /explanation* 127.0.0.1:8000
    reverse_proxy /analytics* 127.0.0.1:8000
    reverse_proxy /coordination* 127.0.0.1:8000
    reverse_proxy /dashboard* 127.0.0.1:8000
    reverse_proxy /widgets* 127.0.0.1:8000
    reverse_proxy /preferences* 127.0.0.1:8000
    reverse_proxy /watchlists* 127.0.0.1:8000
    reverse_proxy /timeline* 127.0.0.1:8000
    reverse_proxy /scanner* 127.0.0.1:8000
    reverse_proxy /terminal* 127.0.0.1:8000
    reverse_proxy /evidence* 127.0.0.1:8000
    reverse_proxy /journal* 127.0.0.1:8000
    reverse_proxy /paper* 127.0.0.1:8000

    # Proxy WebSocket channels (enables instant connection upgrades)
    reverse_proxy /ws/* 127.0.0.1:8000

    # Strong security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://* wss://*; img-src 'self' data:; font-src 'self' data:;"
    }
}
```

*Note: If you use `elite.local`, map it in your hosts file (`/etc/hosts` or `C:\Windows\System32\drivers\etc\hosts`) to point to `127.0.0.1`.*

To run Caddy:
```bash
caddy run --config ./Caddyfile
```

---

### Option B: Nginx Configuration (`nginx.conf`)

For native Nginx deployment, use this robust server configuration:

```nginx
upstream fastapi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name elite.local 127.0.0.1;
    # Force HTTP to HTTPS redirection
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name elite.local 127.0.0.1;

    # SSL Certificates
    ssl_certificate /etc/ssl/certs/elite.crt;
    ssl_certificate_key /etc/ssl/private/elite.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Gzip Compression
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml font/woff2;
    gzip_min_length 256;

    # Frontend compiled assets root
    root /var/www/elite-decision-engine/frontend/dist;
    index index.html;

    # Secure HTTP Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # SPA routing fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static assets long-term cache
    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API Proxying
    location ~ ^/(auth|health|monitoring|notifications|signals|risk|portfolio|position-sizing|performance|backtest|intelligence|trading-control|market|regime|users|explanation|analytics|coordination|dashboard|widgets|preferences|watchlists|timeline|scanner|terminal|evidence|journal|paper) {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    # WebSockets Proxying (Protocol Upgrade)
    location /ws/ {
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 86400; # Keep connections alive
    }
}
```

---

## 6. Automatic Startup Configuration (Service Setup)

Configure the application to run automatically in the background and restart after machine reboots.

### Option A: Linux (Systemd)

1. Create a Systemd service file at `/etc/systemd/system/elite-backend.service`:
   ```ini
   [Unit]
   Description=Elite Decision Engine Backend Service
   After=network.target postgresql.service

   [Service]
   Type=simple
   User=your_username
   WorkingDirectory=/path/to/elite-decision-engine
   EnvironmentFile=/path/to/elite-decision-engine/.env.production
   ExecStart=/path/to/elite-decision-engine/.venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 4 --limit-concurrency 1000
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```
2. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable elite-backend.service
   sudo systemctl start elite-backend.service
   ```

---

### Option B: macOS (Launchd)

1. Create a plist file at `~/Library/LaunchAgents/io.elite.backend.plist`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>io.elite.backend</string>
       <key>ProgramArguments</key>
       <array>
           <string>/path/to/elite-decision-engine/.venv/bin/uvicorn</string>
           <string>api.main:app</string>
           <string>--host</string>
           <string>127.0.0.1</string>
           <string>--port</string>
           <string>8000</string>
           <string>--workers</string>
           <string>4</string>
       </array>
       <key>WorkingDirectory</key>
       <string>/path/to/elite-decision-engine</string>
       <key>EnvironmentVariables</key>
       <dict>
           <key>API_ENV</key>
           <string>production</string>
           <key>DATABASE_URL</key>
           <string>postgresql://elite_admin:SecureAdminPassword123!@localhost:5432/elite_production</string>
           <key>JWT_SECRET</key>
           <string>4f9b88ad39cf5c772be55a5b9e07f918e959635b7cc6d9df262a0a2569faee98</string>
           <key>CORS_ORIGINS</key>
           <string>https://elite.local,https://127.0.0.1</string>
       </dict>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
       <key>StandardOutPath</key>
       <string>/path/to/elite-decision-engine/logs/stdout.log</string>
       <key>StandardErrorPath</key>
       <string>/path/to/elite-decision-engine/logs/stderr.log</string>
   </dict>
   </plist>
   ```
2. Register and launch:
   ```bash
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/io.elite.backend.plist
   ```

---

### Option C: Windows (Task Scheduler)

1. Open **Task Scheduler**.
2. Click **Create Basic Task**. Name it "Elite Decision Engine Startup".
3. Trigger: Set to **When the computer starts**.
4. Action: **Start a program**.
5. Program/script: Browse and select the absolute path to `START_PRODUCTION.bat`.
6. Settings: Check **Run whether user is logged on or not** and select **Run with highest privileges**.

---

## 7. Production Logging

The system manages logging automatically. When `API_ENV=production` is active:
- Standard logs are formatted into **structured JSON** on stdout, making it easy to parse.
- Logs are routed to rotated file handlers inside the local `logs/` directory:
  - `logs/engine.log` — Database transactions, central application startup, and core loops.
  - `logs/trade.log` — Execution records, signals logic, and scoring.
  - `logs/error.log` — Stack traces and serious failures.
- File logs are limited to **10MB** per file and automatically roll over, keeping up to **5 historic backups** to guarantee disk safety.
- Sensitive information (JWT keys, passwords, tokens, API key parameters) is **scrubbed** from logs using regex filters before writing.

---

## 8. Database Backups Configuration

Set up a daily automated backup rotation to safeguard trading performance historical tables.

Create a bash script `scripts/db_backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/path/to/elite-decision-engine/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATABASE_NAME="elite_production"
DB_USER="elite_admin"
EXPORT_PATH="$BACKUP_DIR/${DATABASE_NAME}_$TIMESTAMP.sql"

mkdir -p "$BACKUP_DIR"

# Perform backup
pg_dump -U "$DB_USER" -h localhost "$DATABASE_NAME" > "$EXPORT_PATH"

# Prune backups older than 30 days
find "$BACKUP_DIR" -type f -name "*.sql" -mtime +30 -delete

echo "PostgreSQL backup successfully completed: $EXPORT_PATH"
```

Configure as a cron job (`crontab -e`):
```cron
0 3 * * * /bin/bash /path/to/elite-decision-engine/scripts/db_backup.sh >> /path/to/elite-decision-engine/logs/backup.log 2>&1
```

---

## 9. Rollback Procedure

If a deployment fails, follow these rapid recovery steps to restore operations:

### Step 1: Stop Services
```bash
# macOS/Linux
./STOP_PRODUCTION.sh

# Windows
STOP_PRODUCTION.bat
```

### Step 2: Revert Code & Frontend Assets
Locate your previous known-good git hash:
```bash
# Revert codebase to stable commit
git reset --hard <STABLE_COMMIT_HASH>

# Clean and rebuild frontend assets
npm --prefix frontend clean-install
npm --prefix frontend run build
```

### Step 3: Revert Database Configuration
If a database migration corrupted data, restore from the latest automated SQL backup:
```bash
# Drop corrupt database
dropdb -U elite_admin -h localhost elite_production

# Re-create database
createdb -U elite_admin -h localhost elite_production

# Restore SQL backup
psql -U elite_admin -h localhost elite_production < backups/elite_production_XXXXXXXX_XXXXXX.sql
```

### Step 4: Restart Production Services
```bash
# macOS/Linux
./START_PRODUCTION.sh

# Windows
START_PRODUCTION.bat
```
Verify logs immediately in `logs/engine.log` and visit `https://elite.local` to verify visual layout.
