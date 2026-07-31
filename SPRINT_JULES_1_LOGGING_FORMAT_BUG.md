# Sprint 1/3: Second logging format-string bug (parallel-safe: touches api/websocket, council/, services/coordinator_service.py, services/widget_service.py, api/routes/coordination.py, api/routes/intelligence.py — does not overlap with Sprint 2 or 3)

## Context

Run `pytest tests/ -q` first to confirm the current baseline before you start.

A prior pass already fixed two things on this branch — confirm they're present, don't redo them:
1. `logging_config.py` — `httpx` and `httpcore` loggers set to `WARNING` in `setup_logging()` (root logger was `DEBUG`, which made httpx's own internal request-logging line crash with `TypeError: %d format: a real number is required, not str` when going through Starlette's `TestClient`).
2. `api/main.py` — `api/routes/paper.py`'s router is now imported and `include_router`'d (it previously wasn't wired into the app at all).

**This repo's own docs (`KNOWN_LIMITATIONS.md`, `TECHNICAL_DEBT.md`, `MASTER_BOOK.md`) are unreliable** — several "critical bug" claims in them were checked against actual code and found false or already fixed. Do not use those files as a source of truth for this sprint. Verify everything against actual code and full tracebacks (`pytest path::test_name --tb=long`).

## Your task

The following tests still fail with `TypeError` even after the httpx fix above, meaning there's a **second, separate** bad `logger.xxx("...%d...", wrong_type_arg)` call somewhere in this project's own code (not httpx) — likely a string, `None`, or UUID being passed where `%d` expects an int. Find it and fix the argument (or the format string) in each affected module. Use `--tb=long` on each to get the exact file/line before guessing.

- `tests/test_websocket_manager.py::test_connect_adds_client`, `test_disconnect_removes_client`, `test_broadcast_sends_to_all`, `test_broadcast_removes_stale_clients` → check `api/websocket/manager.py`
- `tests/test_api_main.py::test_websocket_connect_and_disconnect` → likely same root cause as above
- `tests/test_council_consensus.py::TestConsensusEngine::test_register_defaults`, `test_register_agent`, `test_consensus_all_bullish`, `test_consensus_all_bearish`, `test_consensus_split`, `test_consensus_weighted_bullish`, `test_stats` → check `council/consensus.py`
- `tests/test_coordinator_service.py::TestIntelligenceRegistry::test_register_and_list`, `test_register_multiple`, `test_unregister`, `test_get_instance`, `test_mark_error`; `TestCoordinatorService::test_evaluate_with_registered_sources`, `test_conflict_detection`, `test_consensus_agreement_strong` → check `services/coordinator_service.py`
- `tests/test_coordinator_api.py::TestCoordinatorAPI::test_register_source` → check `api/routes/coordination.py`
- `tests/test_batch2_api.py::TestWidgetsAPI::test_get_kpi_widget`, `test_get_portfolio_widget`, `test_get_monitoring_widget` → check `services/widget_service.py` / `api/routes/widgets.py`
- `tests/test_api_routes.py::test_get_intelligence_db_fallback`, `test_get_intelligence_with_trades` → check `api/routes/intelligence.py` or the service it calls

## Acceptance criteria

- All listed tests pass.
- No other currently-passing test in the full suite regresses (`pytest tests/ -q` full run before/after comparison).
- Don't weaken any assertion to make it pass — fix the actual type mismatch.
