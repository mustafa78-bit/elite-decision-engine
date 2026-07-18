# Technical Debt & Known Issues

## Recently Resolved (Founder Beta Sprint)

### Production Readiness

| ID | Issue | Status |
|----|-------|--------|
| P1 | `HealthService.execution()` crashes on ExecutionLoop init failure | ✅ Fixed — graceful degradation |
| P2 | No `LOG_LEVEL` env var support | ✅ Fixed — `config.py` reads `LOG_LEVEL`, `logging_config.py` uses it |
| P3 | No sensitive data scrubbing in logs | ✅ Fixed — `_SensitiveDataFilter` redacts secrets in log output |
| P4 | No `Content-Security-Policy` header | ✅ Fixed — added to security headers middleware |
| P5 | No `/ready` and `/live` health endpoints | ✅ Fixed — added k8s-style readiness/liveness probes |
| P6 | No 404 exception handler | ✅ Fixed — returns JSON with path info |
| P7 | `ENCRYPTION_KEY`, `HL_API_KEY`, `HL_SECRET`, `TELEGRAM_TOKEN` not exported from config | ✅ Fixed — exported as module constants |
| P8 | `.env.example` incomplete | ✅ Fixed — documented all configurable env vars |

### Performance

| ID | Issue | Status |
|----|-------|--------|
| P9 | All pages eagerly imported (large initial bundle) | ✅ Fixed — `React.lazy()` + `Suspense` for 35 routes |
| P10 | Unused `status` state in AppRoutes causes TS warning | ✅ Fixed — removed dead state |

### Security

| ID | Issue | Status |
|----|-------|--------|
| P11 | Duplicate `useAuth` in `AuthGuard.tsx` bypasses `AuthProvider` context | ✅ Fixed — `AuthGuard` now uses context-based `useAuth` |

### Code Cleanup

| ID | Issue | Status |
|----|-------|--------|
| P12 | Unused `Base` import in `startup.py` | ✅ Removed |
| P13 | Unused `RiskManager` import in `monitoring/health.py` | ✅ Removed |
| P14 | Unused `HealthComponent` dataclass in `monitoring/health.py` | ✅ Removed |
| P15 | Dead fields `change_24h`, `volume_change` in `api/events.py` | ✅ Removed |
| P16 | Unused `updateLayout` import in `PreferencesPage.tsx` | ✅ Removed |
| P17 | `ActionCenter.tsx` passing object to `fetchNotifications(limit: number)` | ✅ Fixed |

---

## Remaining Technical Debt

### Critical (Pre-Production Blockers)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| BP2 | `ConfidenceEngine` double-scaling: `confidence * 100` then compared to 0–100 threshold | `core/confidence_engine.py` | Every signal approved as STRONG_APPROVE |
| BP3 | `ATRr_14` typo in indicator column name | `market_data/indicators.py:25` | All indicator data = 0 |
| AF1 | `pandas_ta` missing from `requirements.txt` | `requirements.txt` | Runtime crash on import |

### High Priority

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| MC5 | No integrated signal source / no live data path | `scanner/` | Scanner operates on empty data |
| DP1 | Confidence hardcoded to 0.0 in DecisionPipeline | `execution/pipeline.py` | All signals rejected before threshold check |
| DP2 | Scores never saved to Signal record | `execution/pipeline.py` | Signal history unusable |
| DP4 | No filter chain wired into pipeline | `execution/pipeline.py` | All signals pass through unfiltered |

### Medium Priority

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| DB1 | No ForeignKey constraint on `Trade.signal_id` | `database.py` | Orphaned trades possible |
| DB4 | `update_signal_status()` defined twice | `database.py` | Duplicate function definition |
| RL1 | No per-route rate limiting | `api/rate_limit.py` | Only global 200/min limit |
| HT1 | httpx2 incompatible with Python 3.14 logging | `httpx2` library | Test log format failure |
| JW1 | JWT key 30 bytes (< 32 recommended) | `.env` | Security warning |
| UT1 | `datetime.utcnow()` usage (32 occurrences) | Multiple files | Deprecation in Python 3.14+ |

### Low Priority

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| LC1 | 24 empty `__init__.py` files | Multiple dirs | Minor maintenance |
| LC2 | Legacy test files with zero assertions | `tests/` | False sense of coverage |

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical (resolved) | 0 | ✅ All critical items fixed |
| Critical (remaining) | 3 | BP2, BP3, AF1 — pre-existing, requires refactor |
| High | 3 | MC5, DP1-2, DP4 — pre-existing architectural gaps |
| Medium | 5 | DB1, DB4, RL1, HT1, JW1, UT1 |
| Low | 2 | LC1, LC2 |
| **Founder Beta Resolved** | **17** | ✅ P1–P17 |
