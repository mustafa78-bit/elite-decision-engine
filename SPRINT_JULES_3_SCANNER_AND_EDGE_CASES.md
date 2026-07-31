# Sprint 3/3: Scanner + edge-case test failures (parallel-safe: only touches scanner/core.py, database.py, monitoring/health.py — does not overlap with Sprint 1 or 2)

## Context

Run `pytest tests/ -q` first to confirm the current baseline before you start.

**This repo's own docs (`KNOWN_LIMITATIONS.md`, `TECHNICAL_DEBT.md`, `MASTER_BOOK.md`) are unreliable** — several "critical bug" claims in them were checked against actual code and found false or already fixed. Do not use those files as a source of truth. Verify everything against actual code and full tracebacks (`pytest path::test_name --tb=long`).

## Your task

No root cause has been identified yet for these — investigate from scratch, don't guess without reading the traceback first.

### Scanner (3 failures)
- `tests/test_scanner.py::TestOpportunityScanner::test_scan_with_mock_service`
- `tests/test_scanner.py::TestOpportunityScanner::test_empty_asset_skipped`
- `tests/test_scanner.py::TestOpportunityScanner::test_top_opportunities`

Investigate `scanner/core.py` (`OpportunityScanner` class) against what these tests mock/expect.

### Edge cases (8 failures)
- `tests/test_edge_cases.py::TestSessionScope::test_session_scope_imports`, `test_session_scope_rolls_back_on_error`, `test_session_scope_closes_on_exit` → investigate the session-scope context manager in `database.py`
- `tests/test_edge_cases.py::TestHealthService::test_database_check_returns_dict`, `test_full_returns_all_components`, `test_database_check_returns_latency` → investigate `monitoring/health.py` (`HealthService`)
- `tests/test_edge_cases.py::TestFinalStatuses::test_imported_from_database`, `test_imported_in_paper_executor` → check that `FINAL_STATUSES` is defined identically/importable from both `database.py` and wherever `execution/paper*.py` re-exports or imports it from — likely an import path or naming mismatch after a refactor.

## Acceptance criteria

- All 11 listed tests pass.
- No other currently-passing test regresses.
- Don't weaken assertions to make them pass — find the actual behavior gap between code and test expectation, and if you conclude the *test* is wrong (not the code), say so explicitly in your summary instead of silently changing the test.
