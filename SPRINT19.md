# Sprint 19 — Live Order Lifecycle

## Goal

Implement a complete Live Order Lifecycle model — extend the Trade model, add a `LiveOrderStatus` enum, and persist simulated live orders via `LiveExecutor` — while keeping monitoring read-only and never submitting real exchange orders.

## Deliverables

### 1. `execution/live_order.py` — `LiveOrderStatus` enum

- `str, Enum` — values map directly to the `exchange_status` VARCHAR column without converters.
- Seven values: `NEW`, `PENDING`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `REJECTED`, `EXPIRED`.

### 2. `database.py` — Trade model extension (6 columns)

| Column | Type | Notes |
|---|---|---|
| `client_order_id` | `String(120)` | nullable |
| `exchange_status` | `String(30)` | default `"NEW"` |
| `submitted_at` | `DateTime(timezone=True)` | nullable |
| `updated_at` | `DateTime(timezone=True)` | nullable |
| `filled_at` | `DateTime(timezone=True)` | nullable |
| `average_fill_price` | `Float` | nullable |

All nullable / optional — backward compatible with existing trades.

### 3. `execution/live_executor.py` — `_persist_trade()` method

- Called from `execute()` when `result.accepted is True`.
- Computes TP/SL levels via the injected `TPSLEngine`.
- Creates a `Trade` record with:
  - `exchange_order_id` and `client_order_id` set to the order ID from the exchange response (same UUID in simulation; real adapter would differentiate).
  - `exchange_status` = `"NEW"` (`LiveOrderStatus.NEW.value`).
  - `submitted_at` and `updated_at` = `datetime.now(timezone.utc)`.
  - `pnl = 0.0`, `status = "OPEN"`.
  - `signal_id` from the candidate.
- Opens its own session via the injected `session_factory`, commits on success, rolls back on failure.
- No-op when `session_factory` is `None` (no crash).

### 4. `tests/test_live_executor.py` — 3 new persistence tests

- `test_execute_persists_trade_with_all_fields` — creates a trade, verifies all 14 fields (symbol, side, entry, exchange_order_id, client_order_id, exchange_status, submitted_at, updated_at, pnl, status, stop, tp1, rr, signal_id).
- `test_execute_does_not_persist_when_rejected` — rejected validation does not write a trade.
- `test_execute_no_session_factory_does_not_crash` — no session_factory configured does not crash.

### 5. `tests/test_live_order.py` — 5 enum tests

`TestLiveOrderStatus`: enum values, membership, from-string conversion, str-enum inheritance, all values are strings.

### 6. `tests/conftest.py` — Savepoint removal (cross-test contamination fix)

**Root cause**: SQLAlchemy + SQLite issues `SAVEPOINT` → `RELEASE SAVEPOINT` → `ROLLBACK` at the SQL level, but the `ROLLBACK` does not actually undo savepoint-released INSERTs — data persists across subsequent test connections. This was confirmed by reproducing the exact fixture pattern and examining `sqlalchemy.engine` SQL logging — the `ROLLBACK` statement executes but the leaked row is still visible on fresh connections.

**Fix**: Removed `session.begin(nested=True)` from the `session_factory` fixture. Without savepoints, `session.commit()` flushes data to the connection's outer transaction, and the outer `ROLLBACK` at test teardown properly reverts all changes. All 110 tests now pass in a single run.

## Test Results

```
110 passed in 4.75s
```
