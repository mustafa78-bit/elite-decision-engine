# Sprint 18 — Integrate Adapter into LiveExecutor

## Objective

Wire `HyperliquidReadOnlyAdapter` into `LiveExecutor` to enable read-only monitoring of open positions and orders via the Hyperliquid API. No database modifications. No real orders.

## Architecture

```
LiveExecutor
  ├── execute(candidate, size)
  │     └── ExchangeAdapter.place_order()  ← simulated
  │
  └── monitor_open_trades(address)
        ├── hyperliquid_adapter.get_positions(address)   ← read-only API
        ├── hyperliquid_adapter.get_open_orders(address) ← read-only API
        ├── hyperliquid_adapter.get_current_prices()     ← read-only API
        └── correlate → list[LiveMonitorResult]
              ↑
         Position + OpenOrder → LiveMonitorResult
```

## Execution Flow

```
monitor_open_trades(address)
  │
  ├── 1. get_positions(address)      → list[Position]
  ├── 2. get_open_orders(address)    → list[OpenOrder]
  ├── 3. get_current_prices()        → dict[coin → price]
  │
  └── For each Position:
        ├── Map coin → side (positive size = LONG, negative = SHORT)
        ├── Look up mark price from prices dict
        ├── Look up correlated orders by coin
        ├── Build LiveMonitorResult
        └── Collect into results list
```

## Modified Files

### `execution/hyperliquid_adapter.py` (Sprint 17 file)

**Added** `get_current_prices()` method:
- Calls `type=allMids` endpoint
- Returns `dict[str, float]` mapping coin → mid price
- Read-only, no side effects

### `execution/live_executor.py` (Sprint 16 file)

**Added:**
- `LiveMonitorResult` frozen dataclass:
  - `symbol`, `side`, `size`, `entry_price`, `mark_price`, `unrealized_pnl`, `liquidation_price`, `order_status`, `exchange_order_id`, `timestamp`
- `hyperliquid_adapter` and `address` parameters to `__init__`
- `LONG_SIDE` / `SHORT_SIDE` constants
- `ORDER_SIDE_MAP` for mapping exchange sides ("B"/"A")

**Implemented** `monitor_open_trades()`:
- Guards: returns empty list if no adapter or no address configured
- Fetches positions, orders, prices via injected adapter
- Catches exceptions → logs and returns empty list
- Correlates positions with orders by coin
- Skips zero-size positions
- Returns list of `LiveMonitorResult`

**Added** `_position_to_monitor_result()` helper:
- Extracts coin, size, side from Position
- Looks up mark price from prices dict
- Correlates with pending orders by coin
- Sets order_status to "POSITION" if no pending orders
- Returns `LiveMonitorResult` or `None` for zero-size positions

### No database files modified

SQLAlchemy models, `Trade`, and all DB operations are untouched.

## Test Results

```
102 passed in 2.22s
  - 32 hyperliquid adapter tests
  - 36 live executor tests (12 new monitor tests + 24 existing)
  - 1 integration test
  - 8 portfolio engine tests
  - 9 performance engine tests
  - 7 position sizing tests
  - 9 risk manager tests
```

## New Monitor Tests (12 tests)

| Test | What it verifies |
|------|-----------------|
| `test_monitor_with_adapter_returns_live_monitor_results` | Full monitor flow: positions → orders → prices → LiveMonitorResult |
| `test_monitor_calls_adapter_methods` | All 3 adapter methods called exactly once |
| `test_monitor_empty_positions_returns_empty_list` | No positions → empty results |
| `test_monitor_no_address_returns_empty_list` | No address configured → empty results |
| `test_monitor_no_adapter_returns_empty_list` | No adapter injected → empty results |
| `test_monitor_adapter_error_returns_empty_list` | Adapter raises → empty results (graceful degradation) |
| `test_monitor_short_position_side` | Negative position size → SHORT side |
| `test_monitor_uses_mark_price_from_prices` | Mark price from `get_current_prices()` is used |
| `test_monitor_order_status_position_when_no_orders` | No pending orders → status = "POSITION" |
| `test_live_monitor_result_dataclass` | LiveMonitorResult constructor and field access |
| `test_monitor_zero_size_position_skipped` | Zero-size positions filtered out |

## Safety Guarantees

- **Read-only**: All API calls go through `HyperliquidReadOnlyAdapter` which has no write methods
- **No DB writes**: `monitor_open_trades()` does not modify any database records
- **Graceful degradation**: Adapter errors → logged + empty list returned
- **No real orders**: `execute()` still uses simulated `ExchangeAdapter`
- **No secrets in tests**: All adapters mocked with `MagicMock`

## Remaining Blockers

1. **Live order creation** — `LiveExecutor.execute()` still returns simulated `LiveOrderResult`; no real order is placed
2. **Order persistence** — Live orders are not written to the `Trade` table; no `order_id` field exists on the model
3. **Real API integration test** — No end-to-end test with real Hyperliquid API (intentional, safety first)
4. **Address sourcing** — `address` is passed directly; no wallet address resolution mechanism yet

## Next Recommendation

**Sprint 19: Live Order Persistence & Standalone CLI Monitor**

- Add `order_id` field to the `Trade` SQLAlchemy model
- Persist live orders created by `LiveExecutor.execute()` to the DB
- Expose `LiveExecutor.monitor_open_trades()` through a `python -m engine live` CLI command
- Add wallet address resolution from environment variable (`HL_WALLET_ADDRESS`)
- End-to-end integration test with mocked adapter in `ExecutionLoop` LIVE mode
