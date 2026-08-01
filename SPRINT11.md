# Sprint 11 — Risk Management Engine

## Objective
Design and implement a reusable Risk Management Engine that becomes the single authority deciding whether a trade is allowed to open, sitting between pipeline approval and trade creation.

## Architecture

```
TradingSignal
    ↓
DecisionPipeline  ──→  TradeCandidate or None
    ↓
RiskManager.can_open_trade()  ──→  (True, "") or (False, "reason")
    ↓
TradeEngine.create_trade()  ──→  Trade or None
    ↓
PaperExecutor
```

The `RiskManager` is injected into `ExecutionLoop` via its constructor, same pattern as `DecisionPipeline` and `PaperExecutor`. Each risk rule is checked sequentially; the first violation short-circuits with a logged reason and the signal status is set to `REJECTED`.

## Risk Rules

| # | Rule | Config Key | Default | DB Query |
|---|------|-----------|---------|----------|
| 1 | Max open trades | `MAX_OPEN_TRADES` | 3 | `COUNT WHERE status='OPEN'` |
| 2 | Max exposure per symbol | `MAX_EXPOSURE_PER_SYMBOL` | 200000 | `SUM entry WHERE symbol=X AND status='OPEN'` |
| 3 | Max total portfolio exposure | `MAX_PORTFOLIO_EXPOSURE` | 500000 | `SUM entry WHERE status='OPEN'` |
| 4 | Max daily loss | `MAX_DAILY_LOSS` | 10000 | `SUM pnl WHERE status IN (TP_HIT,SL_HIT,CLOSED) AND closed_at >= today AND pnl < 0` |
| 5 | Max position size | `MAX_POSITION_SIZE_USD` | 100000 | Compares `candidate.entry` against limit |

All five rules are checked in order. Every rejection is logged via `logger.warning()` with the exact reason string.

## Files Modified

### New: `risk_manager.py` (162 lines)
- `RiskManager` class with `can_open_trade(candidate) → tuple[bool, str]`
- Uses `session_factory` pattern (same as `PaperExecutor`) for injectable DB access
- `_check()` method evaluates all 5 rules sequentially

### New: `tests/test_risk_manager.py` (130 lines)
- 9 test cases covering all 5 rules plus edge cases:
  - `test_all_rules_pass` — baseline
  - `test_reject_max_open_trades` — rule 1
  - `test_open_trade_limit_ignores_closed_trades` — rule 1 edge case
  - `test_reject_symbol_exposure` — rule 2
  - `test_allow_different_symbol` — rule 2 negative case
  - `test_reject_portfolio_exposure` — rule 3
  - `test_reject_daily_loss` — rule 4
  - `test_ignore_yesterdays_loss` — rule 4 edge case
  - `test_reject_position_size` — rule 5

### Modified: `config.py`
- Added 4 new config vars: `MAX_EXPOSURE_PER_SYMBOL`, `MAX_PORTFOLIO_EXPOSURE`, `MAX_DAILY_LOSS`, `MAX_POSITION_SIZE_USD`

### Modified: `execution/execution_loop.py`
- Added `risk_manager` parameter to `__init__` (optional, defaults to `RiskManager()`)
- Risk check inserted in `process_signal()` after pipeline approval, before trade creation

### Modified: `tests/test_integration.py`
- Added `RiskManager` import
- Injected `risk_manager=RiskManager(session_factory=session_factory)` into `ExecutionLoop`
- Changed `db_session.commit()` → `db_session.flush()` for SQLite savepoint correctness

### Modified: `tests/conftest.py`
- Removed `PRAGMA journal_mode=WAL` from `_enable_sqlite_pragmas` — WAL mode breaks savepoint-based rollback isolation in SQLite

## Test Results

```
$ python -m pytest tests/ -v
========================= 10 passed, 1 warning in 3.08s =========================
```

Tested consistently across 3 consecutive runs with clean database — zero flakiness.

## Git Diff Summary

### Tracked changes (4 files, +24 -4)
```
 config.py                   |  6 +++++-
 execution/execution_loop.py | 15 +++++++++++++++
 tests/conftest.py           |  3 +--
 tests/test_integration.py   |  4 +++-
```

### New files (untracked)
- `risk_manager.py` — 162 lines
- `tests/test_risk_manager.py` — 130 lines

## Remaining Blockers

None. All risk rules are implemented, tested, and integrated.

## Next Recommendation

**Sprint 12 — Risk rule configuration via environment variables**: Move the 4 new risk configs (and existing `MAX_OPEN_TRADES`) to environment variables with sensible defaults, so they can be tuned per-deployment without code changes.
