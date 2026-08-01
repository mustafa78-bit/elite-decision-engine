# Known Limitations

*Last verified against code: 2026-08-01. Every row below was checked against the current source, not copied from a prior version of this file — several previous "critical bug" claims in this document (an ATR column typo, a `ConfidenceEngine` double-scaling bug, a missing `pandas_ta` dependency, hardcoded confidence in `DecisionPipeline`, and a missing filter chain) were checked directly against the code and found to be false or already fixed. Do not re-add them without re-verifying first.*

## Functional Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No live exchange integration | Only paper trading supported | Use paper executor for validation |
| No signal-level analytics | Cannot analyze signal effectiveness per-signal, only per-trade | Use Trade-level analytics only |
| Council's Macro agent (`council/macro_agent.py`) not yet verified against a real data source | Possible stub/heuristic macro signal | Whale (`market/intelligence/whale.py`) and News (`market/intelligence/news.py`) were verified and upgraded to real Binance/RSS data sources on 2026-07-31; Macro was not part of that pass |
| WebSocket auth dev bypass | In development mode, all WebSocket connections accepted without token | Acceptable for local development |

## Scalability Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| Portfolio engine loads all trades in memory (`portfolio_engine.py`) | Memory pressure at 10k+ trades | Reduce query scope or add pagination |
| No pagination on list endpoints | Degraded UX with large datasets | Acceptable for beta user base |
| No rate limiting per-route (only global) | Susceptible to abuse on specific endpoints | Add per-route limits before production |

## Security Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| JWT key is 30 bytes (< 32 recommended for HS256) | Minor security warning from PyJWT (`InsecureKeyLengthWarning`) | Extend key to 32+ bytes before production |
| Auth tokens stored in `localStorage` | Vulnerable to XSS | Migrate to httpOnly cookies pre-production |
| No CSRF protection | Vulnerable to cross-site requests | Implement double-submit cookie pattern pre-production |
| No account lockout mechanism | Brute force possible on login | Add rate limiting + lockout pre-production |
| Dev mode auto-auth as user_id=1 (`api/middleware.py`) | No real auth in development | Acceptable for local development only |
| No MFA support | Single factor authentication | Add TOTP pre-production |
| Telegram bot has no rate limiting beyond the chat_id whitelist | A whitelisted user could spam `/ask` and burn LLM budget | Add per-user rate limiting if this becomes a problem |

## Technical Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| `datetime.utcnow()` used as a default factory in several models (e.g. `strategies/base.py:19`, `market/models/asset.py:45`, `market/models/ohlcv.py:16`, `exchange/models.py`) | Deprecation warnings in Python 3.12+, will be removed in a future version | Migrate to `datetime.now(timezone.utc)` |
| Empty `__init__.py` files in many package directories | Minor maintenance clutter | Remove or populate as needed |
| Legacy test files with zero assertions | False sense of coverage | Add assertions or remove files |
| No ForeignKey constraint on `Trade.signal_id` | Orphaned trades possible | Add FK constraint in next migration |

## Operational Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| SQLite backend in development | Single-writer, limited concurrency | Use PostgreSQL for production |
| No Alembic migration framework | Manual schema changes | Bootstrap Alembic pre-production |
| CI (`.github/workflows/ci.yml`) only runs on `main`/`execution-layer` branches and PRs into `main` | Work on other branches isn't covered until it's PR'd | Open a PR against `main` to get CI coverage |
| No Prometheus/Grafana monitoring | No operational metrics | Add pre-production |
| No automated alerts | No incident response | Add alerting pre-production |
