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

# Sprint 1/3: Second logging format-string bug (parallel-safe: touches api/websocket, council/, services/coordinator_service.py, api/routes/coordination.py, api/routes/intelligence.py — does not overlap with Sprint 3)

## Context

Run `pytest tests/ -q` first to confirm the current baseline before you start — as of the last verified run it's 29 failed, 1296 passed, 1 skipped.

Already fixed on this branch, confirmed present, don't redo:
1. `logging_config.py` — `httpx`/`httpcore` loggers set to `WARNING`.
2. `api/main.py` — `paper.py` and `simulator.py` routers wired in.
3. `services/widget_service.py` — `**kwargs` added to `_kpi_widget`/`_portfolio_widget`/`_monitoring_widget`.
4. `database.py` — `session_scope()` restored, `FINAL_STATUSES` correctly includes `CANCEL` (4 items).
5. `api/routes/journal.py` — was already correct; the test was wrong and has been fixed to expect 404.

## Your task

The following tests still fail with `TypeError` even after the httpx fix above, meaning there's a **second, separate** bad `logger.xxx("...%d...", wrong_type_arg)` call somewhere in this project's own code (not httpx) — likely a string, `None`, or UUID being passed where `%d` expects an int. Find it and fix the argument (or the format string) in each affected module. Use `--tb=long` on each to get the exact file/line before guessing.

- `tests/test_websocket_manager.py::test_connect_adds_client`, `test_disconnect_removes_client`, `test_broadcast_sends_to_all`, `test_broadcast_removes_stale_clients` → check `api/websocket/manager.py`
- `tests/test_api_main.py::test_websocket_connect_and_disconnect` → likely same root cause as above
- `tests/test_council_consensus.py::TestConsensusEngine::test_register_defaults`, `test_register_agent`, `test_consensus_all_bullish`, `test_consensus_all_bearish`, `test_consensus_split`, `test_consensus_weighted_bullish`, `test_stats` → check `council/consensus.py`
- `tests/test_coordinator_service.py::TestIntelligenceRegistry::test_register_and_list`, `test_register_multiple`, `test_unregister`, `test_get_instance`, `test_mark_error`; `TestCoordinatorService::test_evaluate_with_registered_sources`, `test_conflict_detection`, `test_consensus_agreement_strong` → check `services/coordinator_service.py`
- `tests/test_coordinator_api.py::TestCoordinatorAPI::test_register_source` → check `api/routes/coordination.py`
- `tests/test_api_routes.py::test_get_intelligence_db_fallback`, `test_get_intelligence_with_trades` → check `api/routes/intelligence.py` or the service it calls

## Acceptance criteria

- All listed tests pass.
- No other currently-passing test in the full suite regresses (`pytest tests/ -q` full run before/after comparison).
- Don't weaken any assertion to make it pass — fix the actual type mismatch.
