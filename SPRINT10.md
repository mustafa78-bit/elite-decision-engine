# Sprint 10 — Centralized Logging Infrastructure

## Objective
Build a dedicated logging configuration module that replaces ad-hoc `logging.basicConfig()` with reusable, production-ready setup supporting console output and rotating file handlers with module-level routing.

## Architecture

```
logging_config.py
  └─ setup_logging(log_dir="logs")
       ├─ StreamHandler (console, INFO+)  ← all modules
       ├─ RotatingFileHandler → engine.log (INFO+)  ← core.*, database, app
       ├─ RotatingFileHandler → trade.log (INFO+)  ← execution.*, scoring.*
       └─ RotatingFileHandler → error.log (ERROR+) ← all modules
```

Routing is achieved via `_ModuleFilter` — a logging `Filter` subclass that matches records by logger name prefix (`startswith`). Handlers are attached to the root logger so every child logger propagates upward automatically.

Each file handler rotates at 10 MB with 5 backup copies.

## Files modified

### New: `logging_config.py`
Central configuration module. Exports `setup_logging()` which is idempotent (clears root handlers on each call).

### Modified: `app.py`
- Removed `LOG_FORMAT` constant and `logging.basicConfig()` call.
- Added `from logging_config import setup_logging`.
- `setup_logging()` called at the top of `main()`.

### Modified: `tests/conftest.py`
- Removed `import logging` and `logging.basicConfig()` call.
- Added `from logging_config import setup_logging`.
- `setup_logging()` called at module level so test output uses the same infrastructure.

## Example log output

**logs/engine.log**
```
2026-07-07 06:43:50 [core.engine] INFO     Decision Engine initialized
2026-07-07 06:43:50 [core.engine] INFO     Processing signal BTCUSDT LONG 1h
```

**logs/trade.log**
```
2026-07-07 06:43:50 [execution.pipeline] INFO       Pipeline decision for BTCUSDT LONG 1h: STRONG_APPROVE
2026-07-07 06:43:50 [execution.execution_loop] INFO   Signal approved by decision pipeline: BTCUSDT LONG STRONG_APPROVE
2026-07-07 06:43:50 [execution.execution_loop] INFO   Trade created: BTCUSDT LONG
2026-07-07 06:43:50 [execution.execution_loop] INFO   Monitored 1 open paper trades
2026-07-07 06:43:50 [execution.paper_executor] INFO   Paper trade 1 closed at 52000.00000000 with status TP_HIT
```

**logs/error.log** — empty (no errors during test run)

## Test Results

```
$ python -m pytest tests/ -v
========================= 1 passed, 1 warning in 1.72s =========================
```

All 14 assertions pass. No regressions.

## Git Diff Summary

### Tracked changes (app.py, tests/conftest.py)

```
 app.py            | 5 ++---
 tests/conftest.py | 4 ++--
 2 files changed, 4 insertions(+), 5 deletions(-)
```

`app.py`:
- Remove `LOG_FORMAT` constant
- Replace `logging.basicConfig(...)` with `setup_logging()`

`tests/conftest.py`:
- Remove `import logging`
- Replace `logging.basicConfig(...)` with `setup_logging()`

### New file: `logging_config.py` (untracked)

162 lines. Three public exports: `setup_logging`, `LOG_FORMAT`, `DATE_FORMAT`.

## Remaining Blockers

None.

## Next Recommendation

**Sprint 11 — Log-based monitoring**: Wire `error.log` to a notification channel (e.g., send ERROR-level entries to Slack or email via a background consumer). Alternatively, add structured JSON logging (logfmt format) for machine-parsable output in production.
