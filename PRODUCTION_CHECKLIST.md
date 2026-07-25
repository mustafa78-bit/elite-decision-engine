# Production Readiness Checklist — Self-Hosted Elite Decision Engine

This checklist is verified for local, self-hosted workstation production environments (e.g., Windows, macOS, or Linux running on the founder's own hardware).

---

## 1. Environment & Secrets Configuration

- [ ] **`API_ENV`**: Set to `production` (enforces JSON logging, stricter security headers, and disables development bypass).
- [ ] **`JWT_SECRET`**: Generated as a high-entropy string of at least 32 bytes (256-bit). *Never* use default/development secrets in production.
- [ ] **`ENCRYPTION_KEY`**: Set to a unique, cryptographically secure key for decrypting secure data (e.g., API keys).
- [ ] **`DATABASE_URL`**: Set to a production-grade PostgreSQL instance (`postgresql://user:pass@host:5432/dbname`). SQLite is NOT used in production.
- [ ] **`CORS_ORIGINS`**: Explicitly set to the custom domain or local workstation interface (e.g., `https://elite.local` or `https://127.0.0.1`). Wildcards are disabled.
- [ ] **No Hardcoded Credentials**: Checked and verified that all database, API key, and JWT secrets are injected purely via environment variables.

---

## 2. Reverse Proxy & HTTPS Hardening

- [ ] **SSL/TLS Configuration**: Reverse proxy (Caddy or Nginx) is configured with HTTPS enabled.
  - *Caddy*: Configured for automatic local HTTPS (via Caddy's internal Local CA) or Let's Encrypt for public domains.
  - *Nginx*: Configured with valid SSL certificates, high-grade cipher suites, and modern protocols (TLSv1.2, TLSv1.3).
- [ ] **Static File Delivery**: Reverse proxy is configured to serve static assets from the `frontend/dist` directory directly (leveraging Nginx/Caddy's native speed rather than routing static assets through python).
- [ ] **Proxy Headers**: Appropriate forwarding headers are set:
  - `X-Real-IP` and `X-Forwarded-For` to propagate client IP addresses.
  - `X-Forwarded-Proto` set to `https` to signal downstream components.
  - `Host` header set correctly.
- [ ] **Security Headers**: Production-grade HTTP headers are configured on the proxy:
  - `Strict-Transport-Security` (HSTS) with a 1-year duration.
  - `X-Frame-Options: DENY` (or `SAMEORIGIN`).
  - `X-Content-Type-Options: nosniff`.
  - Content Security Policy (CSP) restricts script and connect origins securely.
- [ ] **WebSocket Upgrades**: Reverse proxy supports HTTP/1.1 protocol upgrades for WebSocket connections on `/ws/*` paths.

---

## 3. Database Production Preparedness

- [ ] **PostgreSQL Connectivity**: Verified that the database is running, reachable, and accepts connections on standard port `5432`.
- [ ] **Schema Migrations**: Schema creation is handled safely. Table structures are fully synchronized with the database models.
- [ ] **Transactional Safety**: Programmatic database operations utilize `session_scope()` contexts to prevent connection leaks or uncommitted state.
- [ ] **Foreign Keys**: Enforced at the database layer (unlike SQLite configurations).
- [ ] **Index Verification**: Critical indexes on signals (`symbol`, `status`), trades, user settings, and watchlists are initialized.

---

## 4. Production Logging & Observability

- [ ] **Rotational Log Files**: Log rotation is configured to prevent disk space exhaustion:
  - `logs/engine.log` (core, DB, app) capped at 10 MB with 5 backups.
  - `logs/trade.log` (execution, scoring) capped at 10 MB with 5 backups.
  - `logs/error.log` (all ERROR+ logs) capped at 10 MB with 5 backups.
- [ ] **Console JSON Logging**: Enabled automatically in production (`API_ENV=production`) for standard structured log aggregation.
- [ ] **Sensitive Data Masking**: Log streams are filtered to automatically mask credentials, secrets, Bearer tokens, and API keys.
- [ ] **Request ID Tracing**: Every incoming HTTP request is assigned a unique `X-Request-ID` header, propagated through logs and responses to facilitate debugging.

---

## 5. Automation, Startup & Recovery

- [ ] **Production Launch Scripts**: Cross-platform startup scripts (`START_PRODUCTION.sh` / `START_PRODUCTION.bat`) are fully operational.
- [ ] **Process Cleanup Scripts**: Cross-platform shutdown scripts (`STOP_PRODUCTION.sh` / `STOP_PRODUCTION.bat`) terminate all backend and proxy processes.
- [ ] **Automatic Service Restart**: Native startup tasks or services configured to automatically launch the application on system boot (e.g., systemd, launchd, or Windows Task Scheduler).
- [ ] **Graceful Rollback Procedure**: Documented steps to restore files, frontend assets, database backups, and environment configurations to a previous known-good state.
- [ ] **Automated Backup Strategy**: Regular cron/task schedules to dump the production PostgreSQL database safely to a secure local folder or S3 bucket.
- [ ] **Health Checks**: Automated script or endpoint tests to continuously monitor backend service, DB ping, and proxy response.
