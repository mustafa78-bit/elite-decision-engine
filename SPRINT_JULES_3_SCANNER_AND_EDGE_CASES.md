STANDING RULES (apply to this entire sprint):

1. Never trust this repo's own markdown docs (KNOWN_LIMITATIONS.md, TECHNICAL_DEBT.md,
   MASTER_BOOK.md, PROJECT_STATUS.md, etc.) as ground truth. They have repeatedly been
   found stale or simply wrong. Verify every claim — including claims in THIS sprint
   doc — against the actual current code and by running the actual test with a full
   traceback (`pytest path::test --tb=long`) before acting on it.

2. When a test fails, first determine WHICH is wrong: the test's expectation, or the
   code's behavior. Do not default to changing whichever is easier to change. If you
   change a shared constant, enum, threshold, or weight to make a test pass, you must
   first grep for every other place that value is used/imported and confirm your
   change doesn't alter behavior there. State in your summary that you did this check
   and what you found.

3. Never modify a test's assertion to match broken/wrong code just to turn it green.
   If you believe the test itself is outdated or asserting the wrong thing, say so
   explicitly in your summary with your reasoning.

4. You must work on your own branch and open a Pull Request against `main`. Never
   push directly to `main`. Do not report a task as "done" until there is a real PR
   with a real diff — a chat summary of what you did is not sufficient.

5. Before claiming "all tests pass" or "N failures fixed", actually run
   `pytest tests/ -q` yourself and paste the real final line (`X failed, Y passed`)
   in your summary. A prior report on this exact sprint claimed "1,325+ passing, zero
   failures" when the real number was 29 still failing — don't repeat that.

6. In your final summary, list the exact files you changed, one line per file
   describing the change and why.

# Sprint 3/3: Scanner + HealthService test failures (parallel-safe: only touches scanner/core.py, monitoring/health.py — does not overlap with Sprint 1)

## Context

Run `pytest tests/ -q` first to confirm the current baseline before you start — as of the last verified run it's 29 failed, 1296 passed, 1 skipped.

Already fixed on this branch, confirmed present, don't redo: `database.py`'s `session_scope()` context manager and `FINAL_STATUSES` (correctly includes `CANCEL`, 4 items) — `TestSessionScope` and `TestFinalStatuses` in `tests/test_edge_cases.py` now pass. Only `TestHealthService` in that file is still failing (see below).

## Your task

No root cause has been identified yet for these — investigate from scratch, don't guess without reading the traceback first.

### Scanner (3 failures)
- `tests/test_scanner.py::TestOpportunityScanner::test_scan_with_mock_service`
- `tests/test_scanner.py::TestOpportunityScanner::test_empty_asset_skipped`
- `tests/test_scanner.py::TestOpportunityScanner::test_top_opportunities`

Investigate `scanner/core.py` (`OpportunityScanner` class) against what these tests mock/expect.

### HealthService (3 failures)
- `tests/test_edge_cases.py::TestHealthService::test_database_check_returns_dict`, `test_full_returns_all_components`, `test_database_check_returns_latency` → investigate `monitoring/health.py` (`HealthService`)

## Acceptance criteria

- All 6 listed tests pass.
- No other currently-passing test regresses.
- Don't weaken assertions to make them pass — find the actual behavior gap between code and test expectation, and if you conclude the *test* is wrong (not the code), say so explicitly in your summary instead of silently changing the test.
