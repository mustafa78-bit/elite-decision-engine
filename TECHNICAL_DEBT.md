# Technical Debt & Known Issues

## Pre-existing Issues (Unchanged)

| ID | Issue | Priority | Impact |
|----|-------|----------|--------|
| BP2 | `ConfidenceEngine` always returns `STRONG_APPROVE` (math bug: `confidence * 100` double-scaling) | **Critical** | Every signal approved |
| BP3 | `ATRr_14` typo in `market_data/indicators.py:25` | **Critical** | All indicator data zero |
| MC5 | No integrated signal source | **High** | No live data path |
| DP1-4 | Confidence hardcoded to 0.0; scores never saved to Signal record | **High** | Lost data |
| PL1-6 | 6 placeholder/filter stubs | **Medium** | Dead code paths |
| DC1-9 | 9 dead code artifacts | **Low** | Maintenance burden |
| DB1 | No FK on `Trade.signal_id` | **Medium** | Orphaned trades |
| DB4 | `update_signal_status()` defined twice | **Low** | Works but confusing |
| AF1 | `pandas_ta` missing from `requirements.txt` | **Critical** | Runtime crash |
| TA1-7 | Zero assertions in 8 legacy test files | **Medium** | No coverage |

## Remaining Issues After Epics 6–8

| ID | Issue | Location | Priority | Status |
|----|-------|----------|----------|--------|
| 6-1 | No rate limiting on API endpoints | All public routes | **Medium** | Unaddressed |
| 6-2 | No ForeignKey constraints on DB models | `models/trade.py` | **Medium** | Pre-existing (DB1) |
| 6-3 | No query pagination on list endpoints | All routes | **Low** | Acceptable for v1 |
| 6-4 | portfolio_engine.py loads all trades into memory | `portfolio_engine.py:91` | **Low** | 1000s of trades only |
| 6-5 | 24 empty `__init__.py` files | All packages | **Low** | Python packaging standard |
| 6-6 | Legacy `datetime.utcnow()` deprecation warnings | Multiple modules (32 occurrences) | **Low** | Python 3.14 compat |
| 6-7 | JWT key length below recommendation (31 bytes) | `api/auth.py` | **Low** | Works but warns |
| 6-8 | websocket broadcast runs unconditionally every 30s | `services/trade_engine.py` | **Low** | No active clients check |
| 6-9 | test_edge_cases.py: 670 lines | `tests/test_edge_cases.py` | **Low** | Refactoring opportunity |
| 6-10 | test_api_routes.py: 53 tests | `tests/test_api_routes.py` | **Low** | Could split by route |

## New Issues Introduced (Minor)

| ID | Issue | Location | Rationale |
|----|-------|----------|-----------|
| N1 | ExplanationService has no real engine dependencies injected | `services/explanation_service.py` | Uses stub data; works for API contract testing but not production decisions |
| N2 | CoordinatorService is stateless (no real AI sources) | `services/coordinator_service.py` | Registry works but sources are dummy until wired to actual intelligence modules |
| N3 | AnalyticsService reads from Trade table only | `services/analytics_service.py` | No Signal-level analytics; correct by design for v1 |
| N4 | Dashboard endpoints duplicate some analytics/explanation data | `api/routes/dashboard.py` | Aggregation layer; intentional overlap for frontend convenience |
| N5 | No pagination on list endpoints | All new routes | Acceptable for v1; data volumes are small |

## Fixes Applied During Implementation

| Issue | Fix |
|-------|------|
| Route ordering: `/coordinate/sources` matched `{signal_id}` param | Moved static routes before parameterized routes |
| `_daily_loss` offset-naive vs aware datetime comparison | Made `today` tz-naive for DB compatibility |
| ATR impact threshold mismatch | Adjusted from `>700` to `>300` for "moderate" |
| Tracked `.pyc` + `.pyo` files in git | Removed from tracking, added patterns to `.gitignore` |
| `datetime.utcnow()` deprecation in `performance_engine.py` | Replaced with `datetime.now(datetime.UTC)` |
| Inefficient Python-side filtering in `performance_engine.py` | Moved filtering to SQL query level |
| `FastAPIDeprecationWarning: regex -> pattern` in scanner routes | Updated `regex` to `pattern` in `Query` params |

## Recommendations

1. **Critical (before production):** Fix `ConfidenceEngine` math bug and `ATRr_14` typo
2. **High:** Wire real dependencies into ExplanationService and CoordinatorService
3. **Medium:** Add `pandas_ta` to `requirements.txt`, add FK constraint, add rate limiting, remove dead code
4. **Low:** Normalize logging, add pagination (`issues 6-8, 6-9, 6-10`), resolve utcnow deprecation across codebase, increase JWT key length, prune unused dependencies, condition websocket broadcast on active clients
