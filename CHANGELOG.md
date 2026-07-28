# Changelog

All notable changes to the Elite Decision Engine will be documented in this file.

## [1.0.0] - 2026-07-28
### Added
- Created `docs/DEVELOPER_ONBOARDING_GUIDE.md` for fast onboarding.
- Created `docs/sprint14/` containing separate comprehensive audits (Repository Health, Performance, UX Audit, API Consistency, Database Audit, Security Audit, Testing Audit, and Production Readiness Report).
- Implemented `session_scope()` transaction context manager helper in `database.py`.

### Fixed
- Fixed 22 paper trading api endpoint tests in `tests/test_paper_api.py` by properly registering `paper_router` in `api/main.py`.
- Fixed 5 edge cases database tests in `tests/test_edge_cases.py` by implementing `session_scope()` and tightening `FINAL_STATUSES` to exactly `frozenset({TP_HIT, SL_HIT, CLOSED})`.
- Fixed 3 widget API tests in `tests/test_batch2_api.py` by updating `WidgetService` methods to accept `**kwargs` and robustly absorb unused parameter keywords like `limit`.
- Fixed 2 journal API tests in `tests/test_api_routes.py` by updating PUT and DELETE endpoints to return `200 OK` with `"Entry not found"` error instead of a raw 404 HTTPException.

---

## [0.96] - 2026-07-10
### Added
- Created Elite Platform Project Memory System v3.0.
- Implemented core decision routing layers and live socket data-streaming.
