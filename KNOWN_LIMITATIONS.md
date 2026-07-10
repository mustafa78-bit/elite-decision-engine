# Known Limitations

## Functional Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No live exchange integration | Only paper trading supported | Use paper executor for validation |
| ConfidenceEngine math bug (double-scaling) | Every signal approved at STRONG_APPROVE | Manual review of all signals |
| ATRr_14 typo breaks indicator pipeline | All indicator data reads as zero | Fix in next patch |
| No signal-level analytics | Cannot analyze signal effectiveness | Use Trade-level analytics only |
| Intelligence sources are stub/wired with dummy data | No real market intelligence | Extended for production wiring |

## Scalability Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| Portfolio engine loads all trades in memory | Memory pressure at 10k+ trades | Reduce query scope or add pagination |
| No pagination on list endpoints | Degraded UX with large datasets | Acceptable for v1 user base |
| No rate limiting on API | Susceptible to abuse | Add middleware before production |
| WebSocket broadcast runs unconditionally every 30s | Wasted resources with no clients | Condition on active connections |

## Security Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| JWT secret key length 31 bytes (≥32 recommended) | Cryptographic weakness warning | Regenerate key before production |
| No ForeignKey on Trade.signal_id | Orphaned trades possible | Add constraint in migration |

## Maintainability Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| 32 datetime.utcnow() deprecation warnings | Python 3.14 breakage | Migrate all to datetime.now(UTC) |
| 7 legacy test files with zero assertions | Confidence gap in legacy code | Add assertions incrementally |
| 24 empty __init__.py files | Noise in repo | Python packaging standard; harmless |
| Dead code artifacts (DC1-9) | Maintenance burden | Remove in scheduled cleanup |
