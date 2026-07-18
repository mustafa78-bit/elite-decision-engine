# Known Limitations

## Functional Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No live exchange integration | Only paper trading supported | Use paper executor for validation |
| `ConfidenceEngine` math bug (double-scaling: `confidence * 100`) | Every signal approved at `STRONG_APPROVE` | Manual review of all signals before execution |
| `ATRr_14` typo breaks indicator pipeline (`market_data/indicators.py:25`) | All indicator data reads as zero | Fix typo in next patch |
| No signal-level analytics | Cannot analyze signal effectiveness | Use Trade-level analytics only |
| Intelligence sources are stub/wired with dummy data | No real market intelligence | Extended for production wiring |
| WebSocket auth dev bypass | In development mode, all WebSocket connections accepted without token | Acceptable for local development |

## Scalability Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| Portfolio engine loads all trades in memory (`portfolio_engine.py`) | Memory pressure at 10k+ trades | Reduce query scope or add pagination |
| No pagination on list endpoints | Degraded UX with large datasets | Acceptable for beta user base |
| No rate limiting per-route | Susceptible to abuse on specific endpoints | Add per-route limits before production |

## Security Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| JWT key is 30 bytes (< 32 recommended for HS256) | Minor security warning from PyJWT | Extend key to 32+ bytes before production |
| Auth tokens stored in `localStorage` | Vulnerable to XSS | Migrate to httpOnly cookies pre-production |
| No CSRF protection | Vulnerable to cross-site requests | Implement double-submit cookie pattern pre-production |
| No account lockout mechanism | Brute force possible on login | Add rate limiting + lockout pre-production |
| Dev mode auto-auth as user_id=1 | No real auth in development | Acceptable for local development only |
| No MFA support | Single factor authentication | Add TOTP pre-production |

## Technical Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| `httpx2` incompatible with Python 3.14 logging `%d` format | Test log formatting fails | Pin Python version or patch httpx2 |
| `datetime.utcnow()` used in 32 locations | Deprecation warnings in Python 3.14+ | Migrate to `datetime.now(timezone.utc)` |
| 24 empty `__init__.py` files | Minor maintenance clutter | Remove or populate as needed |
| Legacy test files with zero assertions | False sense of coverage | Add assertions or remove files |
| No ForeignKey constraint on `Trade.signal_id` | Orphaned trades possible | Add FK constraint in next migration |

## Operational Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| SQLite backend in development | Single-writer, limited concurrency | Use PostgreSQL for production |
| No Alembic migration framework | Manual schema changes | Bootstrap Alembic pre-production |
| No CI/CD pipeline | Manual deployment only | Set up GitHub Actions pre-production |
| No Prometheus/Grafana monitoring | No operational metrics | Add pre-production |
| No automated alerts | No incident response | Add alerting pre-production |
