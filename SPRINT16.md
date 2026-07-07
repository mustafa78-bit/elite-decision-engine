# Sprint 16 — Live Trading Foundation

## Objective

Build the complete architecture required for live execution while remaining 100% safe. No real orders are ever sent.

## Architecture

```
DecisionPipeline
    ↓
RiskManager
    ↓
PositionSizing
    ↓
ExecutionRouter  ← TradingMode (PAPER | LIVE)
   ╱        ╲
PAPER       LIVE
Executor    Executor
   ↓           ↓
Trade(DB)   Simulated
            Exchange
```

## Execution Flow

```
process_signal(signal)
  → pipeline.evaluate(signal)           → TradeCandidate or None
  → risk_manager.can_open_trade(candidate) → (bool, reason)
  → position_sizer.calculate(candidate) → PositionSize
  → execution_router.execute(candidate, size)
      ├─ LIVE:  LiveExecutor.execute()  → LiveOrderResult
      └─ PAPER: PaperExecutor.open_trade() → Trade
  → update_signal_status(EXECUTED | OPEN | REJECTED)

monitor()
  → execution_router.monitor_open_trades()
      ├─ LIVE:  LiveExecutor.monitor_open_trades() → list (empty)
      └─ PAPER: PaperExecutor.monitor_open_trades() → list[TradeMonitorResult]
```

## New Files

| File | Lines | Purpose |
|------|-------|---------|
| `execution/live_executor.py` | 174 | LiveExecutor class, LiveOrderRequest, LiveOrderResult, ExchangeAdapter protocol, SimulatedExchangeAdapter |
| `execution/router.py` | 82 | TradingMode enum (PAPER/LIVE), ExecutionRouter class |
| `tests/test_live_executor.py` | 264 | 24 deterministic unit tests |

### execution/live_executor.py

Components:
- **LiveOrderRequest** — frozen dataclass: symbol, side, order_type, price, quantity, stop_loss, take_profit, reduce_only, time_in_force
- **LiveOrderResult** — frozen dataclass: accepted, mode, exchange, client_order_id, payload, response, error
- **ExchangeAdapter** — Protocol with place_order, cancel_order, get_order_status
- **SimulatedExchangeAdapter** — returns canned responses (NEW/CANCELED/FILLED), no network
- **LiveExecutor** — 5-step execution: validate → build payload → sign placeholder → send via adapter → parse response

Validation checks:
- candidate and size must not be None
- symbol is required
- side must be LONG or SHORT
- entry must be > 0
- quantity must be > 0

Signature is a placeholder string: `SIMULATED_SIGNATURE_PLACEHOLDER`

### execution/router.py

Components:
- **TradingMode** — Enum with PAPER and LIVE values
- **ExecutionRouter** — unified interface

The router:
- Defaults to `TradingMode.PAPER` for backward compatibility
- Routes `execute(candidate, size)` to registered executor
- Routes `monitor_open_trades()` to registered executor
- PAPER mode uses `TPSLEngine` for proper TP/SL calculation, then calls `PaperExecutor.open_trade()`
- LIVE mode raises `RuntimeError` if LiveExecutor not configured

## Modified Files

| File | Change | Lines |
|------|--------|-------|
| `execution/execution_loop.py` | Added `execution_router` parameter, `_execute()` method, router-aware `monitor()` | +51 |

### execution/execution_loop.py changes

- Added `from execution.router import ExecutionRouter, TradingMode`
- Added `execution_router` parameter to `__init__` (optional, backward compatible)
- Added `_is_success()` helper for checking result acceptance
- Added `_execute()` method — routes through `execution_router` if configured, falls back to `_create_trade()`
- Updated `monitor()` — uses router if configured, falls back to `paper_executor`
- Existing `_create_trade()` preserved for backward compatibility

## Tests

24 new tests across 3 test classes:

### TestSimulatedExchangeAdapter (3 tests)
- `test_place_order_returns_canned_response`
- `test_cancel_order_returns_canceled`
- `test_get_order_status_returns_filled`

### TestLiveExecutor (14 tests)
- `test_execute_valid_trade_returns_accepted`
- `test_execute_rejected_when_candidate_is_none`
- `test_execute_rejected_when_size_is_none`
- `test_execute_rejected_for_bad_side`
- `test_execute_rejected_for_zero_entry`
- `test_execute_rejected_for_zero_quantity`
- `test_execute_payload_contains_correct_fields`
- `test_payload_contains_signature_placeholder`
- `test_payload_contains_timestamp`
- `test_monitor_open_trades_returns_empty_list`
- `test_execute_uses_custom_exchange_adapter`
- `test_live_order_result_dataclass`
- `test_rejected_live_order_result`

### TestExecutionRouter (7 tests)
- `test_default_mode_is_paper`
- `test_live_mode_routes_to_live_executor`
- `test_paper_mode_executes_via_paper_executor`
- `test_live_mode_monitor_returns_empty_list`
- `test_live_mode_without_executor_raises`
- `test_live_mode_monitor_without_executor_raises`
- `test_paper_mode_monitor_uses_paper_executor`
- `test_trading_mode_enum_values`

### Test Results

```
58 passed in 4.72s
  - 34 existing tests (unchanged)
  - 24 new tests (live executor + router)
```

## Git Diff (Sprint 16 only)

```
 execution/execution_loop.py   |  51 ++++++++++++-
 execution/live_executor.py    | 174 ++++++++++++++++++++++++++++++++++
 execution/router.py           |  82 ++++++++++++++++
 tests/test_live_executor.py   | 264 ++++++++++++++++++++++++++++++++++++++++++
 4 files changed, 571 insertions(+)
```

## Backward Compatibility

- `ExecutionLoop.__init__` gains optional `execution_router` parameter
- When `execution_router=None` (default), behavior is identical to Sprint 15
- All existing 34 tests pass without modification
- `PaperExecutor` is completely untouched
- `ExecutionRouter` defaults to `TradingMode.PAPER`

## Safety Guarantees

- `LiveExecutor.execute()` NEVER sends exchange orders
- `SimulatedExchangeAdapter` returns canned responses only
- All exchange interactions are intercepted by the `ExchangeAdapter` protocol
- Signature is a placeholder string, not a real cryptographic signature
- No API keys, secrets, or network calls in tests
- Default mode is PAPER, requiring explicit opt-in to LIVE

## Remaining Blockers

1. **Exchange adapter implementation** — `SimulatedExchangeAdapter` must be replaced with a real Hyperliquid API client before live trading
2. **Signature implementation** — `_sign_payload` must implement real HMAC signing with exchange credentials
3. **Order status polling** — `LiveExecutor.monitor_open_trades()` returns empty list; needs actual order status tracking
4. **Live order persistence** — Live orders are not persisted to the database; need Trade records for active live positions
5. **Test coverage for monitor** — No tests yet for the LIVE monitoring path with real order tracking
6. **Secrets management** — LiveExecutor needs access to `HL_API_KEY`/`HL_SECRET` without hardcoding

## Next Recommendation

**Sprint 17: Exchange Adapter & Order Persistence**

- Implement a real Hyperliquid exchange adapter (read-only first, no orders)
- Add `LiveExecutor.monitor_open_trades()` with order status polling
- Persist live orders to DB as Trade records
- Add `order_id` field to Trade model
- Wire `HL_API_KEY` and `HL_SECRET` into the exchange adapter
- Add integration test with mock HTTP responses for Hyperliquid API
