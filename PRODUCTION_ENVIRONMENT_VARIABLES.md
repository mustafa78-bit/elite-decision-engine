# Production Environment Variables Directory

This document details all configuration parameters, environment variables, credential layouts, and fallback defaults for deploying the Elite Decision Engine to production.

---

## 1. Critical Environment Variables (Required)

If any of these variables are missing, the platform will refuse to boot in production mode (`API_ENV=production`) and raise a fatal `RuntimeError`.

| Variable Name | Description | Example Value | Boot Action if Missing |
| :--- | :--- | :--- | :--- |
| **`JWT_SECRET`** | Secret key for signing and verifying JSON Web Tokens (JWT) for API auth. Must be at least 32 bytes. | `e18e3a24b...` | **FATAL**. Platform raises `RuntimeError` and exits immediately. |
| **`DATABASE_URL`** | The full SQLAlchemy-compatible connection string for PostgreSQL production DB. | `postgresql://user:pass@host:5432/db` | **FATAL** in production mode. Fall back to local SQLite in development. |

---

## 2. Integration Credentials (Optional / Feature-Gated)

These variables enable external live APIs. If unconfigured, their corresponding features are gracefully disabled or degraded, but the core engine remains fully operational in paper mode.

| Variable Name | Integration System | Default / Fallback Behavior if Unset |
| :--- | :--- | :--- |
| **`NVIDIA_API_KEY`** | AI Services (NVIDIA NIM) | Disables active AI generation features; explanations fall back to static templates. |
| **`HL_API_KEY`** | Hyperliquid Live Adapter | Hyperliquid live execution is unavailable; paper trading remains fully active. |
| **`HL_SECRET`** | Hyperliquid Live Adapter | Hyperliquid live execution is unavailable. |
| **`BINANCE_API_KEY`** | Binance Live Adapter | Binance live account execution is unavailable; paper trading remains active. |
| **`BINANCE_API_SECRET`** | Binance Live Adapter | Binance live execution is unavailable. |
| **`TELEGRAM_TOKEN`** | Notifications Subsystem | Telegram notification dispatch is skipped; websocket alerts remain active. |
| **`TELEGRAM_CHAT_ID`** | Notifications Subsystem | Telegram notification dispatch is skipped. |

---

## 3. Engine Control Parameters (Optional)

These variables adjust the core decision pipeline, risk boundaries, and execution rates.

| Variable Name | Default Value | Allowed Range | Description |
| :--- | :--- | :--- | :--- |
| **`API_ENV`** | `development` | `development`, `production` | Switches log verbosity and critical dependency checks. |
| **`LOG_LEVEL`** | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Controls logging detail output across log files. |
| **`CHECK_INTERVAL`** | `10` | `> 0` | The evaluation loop cycle rate in seconds. |
| **`MIN_SCORE`** | `85` | `0` to `100` | Gating score required for a signal to be sent to risk assessment. |
| **`MAX_OPEN_TRADES`** | `3` | `>= 0` | Maximum parallel open trades permitted. |
| **`MAX_DAILY_LOSS`** | `10000` | `>= 0` | Maximum absolute loss in USD allowed in a rolling 24h period. |
| **`ACCOUNT_EQUITY`** | `10000` | `> 0` | Virtual baseline account size in USD for paper trading. |

---

## 4. Default Fallbacks Configuration

The platform is designed to be **fault-tolerant by design**. If any upstream live integrations fail, the system stays online:
1. **Exchange connection lost:** Adapter raises caught exceptions; UI displays "Dormant / Local Connection".
2. **PostgreSQL unreachable:** Logs warning, and gracefully falls back to local file-based SQLite database.
3. **AI Provider rate-limited:** Returns cached or pre-baked template signal explanations.
