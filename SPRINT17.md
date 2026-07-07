# Sprint 17 — Read-Only Hyperliquid Adapter

## Objective

Implement a read-only Hyperliquid API adapter for account queries. All HTTP calls are mock-tested. No orders are ever created, cancelled, or modified.

## API Coverage

| Method | Hyperliquid `/info` type | Read-Only |
|--------|-------------------------|-----------|
| `get_account_state(address)` | `clearinghouseState` | ✅ |
| `get_open_orders(address)` | `openOrders` | ✅ |
| `get_positions(address)` | `clearinghouseState` → positions | ✅ |
| `get_balance(address)` | `clearinghouseState` + `spotAssets` | ✅ |
| `get_exchange_status()` | `exchangeStatus` | ✅ |
| `get_metadata()` | `meta` | ✅ |
| `get_order_status(address, order_id)` | `orderStatus` | ✅ |
| `place_order(payload)` | — | ❌ YASAK |
| `cancel_order(order_id)` | — | ❌ YASAK |
| `modify_order(...)` | — | ❌ YASAK |
| `close_position(...)` | — | ❌ YASAK |

## New File

### `execution/hyperliquid_adapter.py` (207 lines)

```
HyperliquidReadOnlyAdapter
  ├── get_account_state()     → AccountState
  ├── get_open_orders()       → list[OpenOrder]
  ├── get_positions()          → list[Position]
  ├── get_balance()            → list[Balance]
  ├── get_exchange_status()    → ExchangeStatus
  ├── get_metadata()           → dict
  ├── get_order_status()       → dict
  │
  └── _post(payload)           → raw JSON
         ├── requests.Session.post()
         └── raise_for_status()
```

**Dataclasses:**
- `AccountState` — address, account_value, withdrawable, total_margin, positions, raw
- `OpenOrder` — coin, side, limit_px, sz, order_type, order_id, status, timestamp, raw
- `Position` — coin, size, entry_px, unrealized_pnl, realized_pnl, leverage, liquidation_px, raw
- `Balance` — coin, total, withdrawable, raw
- `ExchangeStatus` — status, contracts_open, raw

**Design decisions:**
- Injectable `requests.Session` for mocking
- Logger injection for testable logging
- `_safe_float()` handles None, strings, and invalid values
- Position parsing supports both nested (`position.coin`) and flat (`coin`) response formats

## Test File

### `tests/test_hyperliquid_adapter.py` (264 lines, 32 tests)

All HTTP calls mocked via `unittest.mock.MagicMock`. No internet, no API, no secrets.

| Category | Tests |
|----------|-------|
| Account state | 4 |
| Open orders | 3 |
| Positions | 2 |
| Balance | 2 |
| Exchange status | 2 |
| Metadata | 2 |
| Order status | 2 |
| HTTP errors | 1 |
| Session defaults | 1 |
| `_safe_float` edge cases | 3 |
| Dataclass construction | 4 |
| Logger verification | 3 |
| Session reuse | 2 |

## Test Results

```
90 passed in 2.16s
  - 32 new tests (hyperliquid adapter)
  - 58 existing tests (unchanged)
```

## No Existing Files Modified

Zero existing files changed. New files only.

## Backward Compatibility

- No existing code is modified
- Adapter is standalone, no imports into existing files
- ExchangeAdapter protocol from Sprint 16 is not modified

## Remaining Blockers

1. **LiveExecutor wiring** — `HyperliquidReadOnlyAdapter` is not yet wired into `LiveExecutor`
2. **Monitor integration** — `LiveExecutor.monitor_open_trades()` still returns empty list; needs adapter integration
3. **Real API testing** — No integration test with real Hyperliquid API (intentional, safety first)
4. **Credentials** — No wallet address or API key management yet

## Next Recommendation

**Sprint 18: Wire Adapter into LiveExecutor**

- Integrate `HyperliquidReadOnlyAdapter` into `LiveExecutor`
- Implement `LiveExecutor.monitor_open_trades()` using adapter
- Fetch real open positions and orders from Hyperliquid
- Add `order_id` field to Trade model for live order tracking
- Full integration test with mocked adapter in LiveExecutor
