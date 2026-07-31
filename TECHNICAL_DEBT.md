# Technical Debt & Known Issues

*Last verified against code: July 31, 2026, not just written from memory/assumption*

This document catalogs verified outstanding technical debt items in the NEXUS Decision Operating System.

## Pre-Production Blockers

The previously claimed critical blockers (`ConfidenceEngine` double-scaling, `ATRr_14` typo in indicator, and missing `pandas_ta` in requirements.txt) have been fully resolved. The remaining architectural/structural gaps include:

| ID | Issue | Location | Impact | Workaround / Status |
|----|-------|----------|--------|---------------------|
| MC5 | No integrated live signal source / no live data path | `scanner/` | Scanner operates on static/paper data only. | Use paper mock data; require live API integrations pre-production. |
| DP1 | Confidence hardcoded to 0.0 in DecisionPipeline | `execution/pipeline.py` | Potential issue in customized paths. (Evaluated with `ConfidenceEngine` for regular signals). | Ensure the `ConfidenceEngine` is always injected/active. |
| DP2 | Scores never saved to Signal database record | `execution/pipeline.py` | Signal history lacks rich component score details. | Add score columns or JSON fields to the `Signal` SQLAlchemy model and persist. |
| DP4 | No filter chain wired into pipeline | `execution/pipeline.py` | All signals pass through unfiltered without pre-evaluation. | Implement robust multi-stage filter steps. |

## Medium Priority

| ID | Issue | Location | Impact | Workaround / Status |
|----|-------|----------|--------|---------------------|
| DB1 | No ForeignKey constraint on `Trade.signal_id` | `database.py` | Orphaned trades or database inconsistency is possible. | Ensure manual transactions handle cascading or define direct relational constraints. |
| DB4 | `update_signal_status()` duplicates | `database.py` | Was previously claimed twice. A single robust definition remains. | Clean and verified; duplicate is completely removed. |
| RL1 | No per-route rate limiting | `api/rate_limit.py` | Only global rate limiting is currently enforced. | Implement route-specific limits on sensitive write operations. |
| JW1 | JWT key 30 bytes (< 32 recommended) | `tests/conftest.py` | Triggers PyJWT InsecureKeyLengthWarning in test suite. | Extend test-secret to 32+ bytes. |
| UT1 | `datetime.utcnow()` usage | Multiple files | Triggers deprecation warnings in Python 3.12+; will break in Python 3.16+. | Change to `datetime.now(timezone.utc)` (active in 19 occurrences). |

## Low Priority

| ID | Issue | Location | Impact | Workaround / Status |
|----|-------|----------|--------|---------------------|
| LC1 | 24 empty `__init__.py` files | Multiple dirs | Minor maintenance/file clutter. | Clean up/remove empty packaging files where modules are already registered. |
| LC2 | Legacy test files with zero assertions | `tests/` | False sense of coverage. | Audit tests and append assertions. |

---

## Technical Debt History

### Sprit 23 UX / Ops Hygiene Resolved
- **Frontend CI/CD Tests Coverage**: Added `npm run test` workflow step under the `frontend` job in `.github/workflows/ci.yml`.
- **Known Limitations & Technical Debt Audit**: Purged disproven/falsely claimed bugs (the ATR column typo, `ConfidenceEngine` double-scaling, and `pandas_ta` requirements claims were all verified as non-existent or previously fixed). Added precise file/line tracking.
