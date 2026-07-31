# Known Limitations

*Last verified against code: July 31, 2026, not just written from memory/assumption*

This document provides a verified, accurate index of known limitations in the NEXUS Decision Operating System.

## Functional Limitations

| Limitation | Impact | Workaround / Context | File Reference |
|------------|--------|----------------------|----------------|
| No live exchange integration | Only paper trading supported. | Use paper executor for validation. | `execution/paper_executor.py` |
| No signal-level analytics | Cannot analyze signal effectiveness on a per-signal basis yet. | Use Trade-level analytics only. | `services/learning/` |
| Intelligence sources are stub/wired with dummy data | No real market intelligence. | Extended for production wiring. | `services/intelligence/` |
| WebSocket auth dev bypass | In development mode, all WebSocket connections are accepted without token validation. | Acceptable for local development, disabled in production. | `api/websocket/manager.py` |

## Scalability Limitations

| Limitation | Impact | Workaround / Context | File Reference |
|------------|--------|----------------------|----------------|
| Portfolio engine loads all trades in memory | Memory pressure at 10k+ trades. | Reduce query scope or add pagination. | `portfolio_engine.py` |
| No pagination on list endpoints | Degraded UX with extremely large datasets. | Acceptable for current alpha user base. | `api/routes/` |
| No rate limiting per-route | Susceptible to abuse on specific endpoints. | Global rate limiter exists; add per-route limits before production. | `api/rate_limit.py` |

## Security Limitations

| Limitation | Impact | Workaround / Context | File Reference |
|------------|--------|----------------------|----------------|
| Auth tokens stored in `localStorage` | Vulnerable to XSS. | Migrate to httpOnly cookies pre-production. | `frontend/src/auth/` |
| No CSRF protection | Vulnerable to cross-site requests. | Implement double-submit cookie pattern pre-production. | `api/main.py` |
| No account lockout mechanism | Brute force possible on login. | Add rate limiting + lockout pre-production. | `auth/` |
| Dev mode auto-auth as user_id=1 | No real auth in development. | Acceptable for local development only. | `api/routes/auth.py` |
| No MFA support | Single factor authentication. | Add TOTP pre-production. | `auth/` |

## Technical Limitations

| Limitation | Impact | Workaround / Context | File Reference |
|------------|--------|----------------------|----------------|
| `datetime.utcnow` used as default factory | Triggers deprecation warnings in Python 3.12+ (which will become errors in Python 3.16+). | Migrate to `datetime.now(timezone.utc)`. | `strategies/base.py:19`, `market/models/asset.py:45`, `market/models/ohlcv.py:16`, `exchange/models.py:21, 39, 50, 63` |
| Empty `__init__.py` files | 24 empty `__init__.py` files exist in directories like `orders/`, `shadow/`, `simulator/` etc. | Minor maintenance clutter; remove or populate. | Multiple directories |
| Legacy test files with zero assertions | Some older test files have no assertions. | False sense of coverage; add assertions or clean up. | `tests/` |
| No ForeignKey constraint on `Trade.signal_id` | Orphaned trades possible. | Add FK constraint in next migration. | `database.py` |

## Operational Limitations

| Limitation | Impact | Workaround / Context | File Reference |
|------------|--------|----------------------|----------------|
| SQLite backend in development | Single-writer, limited concurrency. | Use PostgreSQL for production. | `database.py` |
| No Alembic migration framework | Manual schema changes. | Bootstrap Alembic pre-production. | `database.py` |
| No Prometheus/Grafana monitoring | No operational metrics. | Add pre-production monitoring tools. | N/A |
| No automated alerts | No incident response. | Add alerting pre-production. | N/A |
