# Health Check & Diagnostics Manual — Self-Hosted Production

This manual provides instructions and quick scripts to verify, monitor, and diagnose the health of your production **Elite Decision Engine** environment.

---

## 1. Quick Endpoints Verification (REST API)

You can check individual system components from your terminal using `curl` or by visiting the endpoints in your browser.

### Basic Application Ping
To check if the FastAPI backend is running and responsive:
```bash
curl -i http://127.0.0.1:8000/health
```
**Expected Response (HTTP 200 OK):**
```json
{
  "status": "ok",
  "service": "elite-decision-engine",
  "env": "production",
  "uptime_seconds": 125.43
}
```

### Detailed Subsystem Diagnostics
To inspect the health of the database, exchange collectors, memory cache, and active errors:
```bash
curl -i http://127.0.0.1:8000/health/details
```
**Expected Response Structure:**
```json
{
  "status": "ok",
  "environment": "production",
  "uptime_seconds": 125.43,
  "database": {
    "status": "connected",
    "details": "PostgreSQL"
  },
  "collector": {
    "status": "connected",
    "details": "Hyperliquid API Connection established"
  },
  "database_tables": {
    "status": "healthy",
    "verified_tables": ["signals", "trades", "users", "user_settings", "notifications", "watchlists", "journal_entries", "paper_orders", "paper_trades", "decision_explanations"]
  },
  "errors": null
}
```
*Note: If there are any database connectivity issues or missing schemas, `database.status` will be set to `"error"` or `"degraded"`, and the detailed issues will be listed in the `"errors"` field.*

---

## 2. Reverse Proxy & HTTPS Verification

Verify that Caddy/Nginx is correctly routing traffic, serving compiled static assets, compressing payloads, and enforcing security policies.

### SSL/TLS and HTTP Headers Check
```bash
curl -Iv https://127.0.0.1
```
**Verification Points:**
1. **SSL Handshake**: Verify the handshake succeeds using TLS 1.2 or TLS 1.3.
2. **Static Asset Resolution**: Check that the index HTML is returned with `Content-Type: text/html`.
3. **Response Headers**:
   - `Strict-Transport-Security: max-age=31536000` (Enforces HTTPS).
   - `X-Frame-Options: DENY` (Protects against clickjacking).
   - `X-Content-Type-Options: nosniff` (Prevents MIME-sniffing).
4. **Encoding/Compression**: Verify `Content-Encoding: gzip` or `Content-Encoding: br`/`zstd` is present on static text/JS/CSS assets.

---

## 3. Real-time Live Streams Check (WebSockets)

WebSockets are critical for the real-time workstation experience (trades feeds, dashboard counters, scanner metrics).

You can use the command-line utility `wscat` (installed via `npm install -g wscat`) or a simple browser utility to check socket connectivity.

### Check Trade Activity WS Room:
```bash
wscat -c wss://127.0.0.1/ws/trades
```
### Check Main Dashboard WS Room:
```bash
wscat -c wss://127.0.0.1/ws/dashboard
```
**Expected Output:**
Once connected, you should see:
```
connected (press CTRL+C to quit)
```
And every 30 seconds, uvicorn will broadcast serialized market objects:
```json
{"event_type": "market_update", "payload": {"price": 64230.5, "regime": "BULLISH", "btc_health_score": 1.0, "volatility": 0.045}}
```

---

## 4. Production Log Verification

Ensure that rotational logging is working correctly and that secrets are scrubbed.

### Check Rotating Log Paths
Ensure the log files exist and are populated under the `logs/` directory:
- `logs/engine.log` — core transactions, engine startup, and database.
- `logs/trade.log` — indicators updates, signal evaluation, and order execution.
- `logs/error.log` — database exceptions or system crashes (should be empty under optimal state).

### Verification of Rotational Limits
Run a quick check to see that log sizes are constrained:
```bash
ls -lh logs/
```
Verify that no log file exceeds **10 MB**. If a file reaches 10 MB, a backup (e.g., `logs/engine.log.1`) will automatically be created.

### Verification of Sensitive Data Masking
Search through your logs to confirm that all sensitive credentials are automatically masked:
```bash
# Check if any plain text JWT Secret is written (should yield 0 or only masked occurrences)
grep -in "jwt_secret" logs/*.log

# Check if any API token or keys are exposed
grep -in "key=" logs/*.log
```
The logging configuration uses the custom filter `_SensitiveDataFilter` to replace tokens with `***` automatically, keeping credentials safe.

---

## 5. Troubleshooting Common Production Failures

### 1. Port 80/443 or Port 8000 Already in Use
- **Symptom**: Startup fails stating "Address already in use".
- **Resolution**:
  - For Unix: Find the blocking process using `lsof -i :8000` or `lsof -i :443` and terminate it using `kill -9 <PID>`.
  - For Windows: Find the process using `netstat -ano | findstr :8000` or `netstat -ano | findstr :443` and run `taskkill /F /PID <PID>` in an Administrator CMD.

### 2. Database Connection Authorization Failed
- **Symptom**: `logs/stderr.log` or `logs/engine.log` shows `password authentication failed for user "elite_admin"` or `Connection refused`.
- **Resolution**:
  - Verify that the PostgreSQL service is running: `pg_isready` (Unix) or check "Services" (Windows).
  - Check `.env.production`'s `DATABASE_URL` password matches the database user's password.
  - Verify that the postgres hba configuration (`pg_hba.conf`) permits connections from `127.0.0.1` using md5/scram-sha-256 password methods.

### 3. "Secure Connection Failed" or "Unsecure Site" Warning in Browser
- **Symptom**: Chrome/Safari warns about an untrusted local certificate when visiting `https://elite.local`.
- **Resolution**:
  - If using **Caddy**: Caddy automatically provisions a secure local CA. Make sure Caddy has permissions to write to local system trust stores. Run `caddy trust` in an Administrator terminal to install the CA certificate into your local keychain/root certificate store.
  - If using **Nginx**: Double check that the certificates pointed to by `ssl_certificate` and `ssl_certificate_key` are valid, and install the root CA of those certificates into your local browser's certificate trust store.
