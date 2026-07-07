# Sprint 12 — Position Sizing Engine

## Objective
Implement a standalone Position Sizing Engine that calculates quantity, notional value, and risk amount for every trade before execution.

## Architecture

```
DecisionPipeline → TradeCandidate
    ↓
RiskManager → (True, "") or rejection
    ↓
PositionSizingEngine.calculate(candidate) → PositionSize
    ↓
ExecutionLoop logs result → _create_trade()
```

The `PositionSizingEngine` is injected into `ExecutionLoop` via its constructor, same pattern as `DecisionPipeline`, `RiskManager`, and `PaperExecutor`. It is a pure calculator with no database access and no side effects.

## Formula

```
risk_per_unit      = ATR × ATR_MULTIPLIER
account_risk       = ACCOUNT_EQUITY × RISK_PER_TRADE_PERCENT / 100
raw_quantity       = account_risk / risk_per_unit
notional_value     = raw_quantity × entry_price
```

If `notional_value > MAX_POSITION_SIZE_USD` → clamp `quantity = max(MAX_POSITION_SIZE_USD / entry, MIN_POSITION_QUANTITY)`

If `raw_quantity < MIN_POSITION_QUANTITY` → floor at `MIN_POSITION_QUANTITY`

If `ATR ≤ 0` → return minimum position (safety fallback)

## Example Calculations

| Scenario | Equity | ATR | Entry | Quantity | Notional | Risk $ |
|----------|--------|-----|-------|----------|----------|--------|
| Normal ($10k, 1%) | 10,000 | 500 | 50,000 | 0.1333 | 6,666.67 | 100.00 |
| Small ($500, 1%) | 500 | 500 | 50,000 | 0.0067 | 333.33 | 5.00 |
| Large ($1M, capped) | 1,000,000 | 500 | 50,000 | 2.0 | 100,000.00 | 1,500.00 |
| High ATR (5,000) | 10,000 | 5,000 | 50,000 | 0.0133 | 666.67 | 100.00 |
| Low ATR (50) | 10,000 | 50 | 50,000 | 1.3333 | 66,666.67 | 100.00 |
| Min floor (tiny) | 100 | 5,000 | 50,000 | 0.001 | 50.00 | 7.50 |
| ATR = 0 | 10,000 | 0 | 50,000 | 0.001 | 50.00 | 0.00 |

## Files Modified

### New: `position_sizing.py` (82 lines)

- `PositionSize` dataclass: `quantity`, `notional_value`, `risk_amount`
- `PositionSizingEngine` class with `calculate(candidate)` method
- Configurable via constructor: `account_equity`, `risk_percentage`, `atr_multiplier`, `max_position_usd`, `min_quantity`

### New: `tests/test_position_sizing.py` (86 lines)

7 test cases covering all sizing scenarios.

### Modified: `config.py`

- Added `ACCOUNT_EQUITY = 10000`
- Added `RISK_PER_TRADE_PERCENT = 1.0`
- Added `ATR_MULTIPLIER = 1.5`
- Added `MIN_POSITION_QUANTITY = 0.001`

### Modified: `execution/execution_loop.py`

- Added `position_sizer` parameter to `__init__` (optional, defaults to `PositionSizingEngine()`)
- Added `position_sizer.calculate(candidate)` call in `process_signal()` after risk check passes
- Logs quantity, notional value, and risk amount

## Tests

```
$ python -m pytest tests/ -v
========================= 17 passed, 1 warning in 3.84s =========================
```

- `test_normal_account` — baseline 1% risk trade
- `test_small_account` — tiny equity produces small quantity
- `test_large_account_caps_notional` — $1M equity caps at $100K max notional
- `test_high_atr_smaller_position` — wide ATR reduces quantity
- `test_low_atr_larger_position` — narrow ATR increases quantity
- `test_minimum_quantity_floor` — extreme risk/ATR ratio floors at 0.001
- `test_zero_atr_uses_minimum` — ATR=0 safety fallback

## Git Diff

### Tracked changes (2 files, +18 -1)
```
 config.py                   | 6 +++++-
 execution/execution_loop.py | 13 +++++++++++++
```

### New files (untracked)
- `position_sizing.py` — 82 lines
- `tests/test_position_sizing.py` — 86 lines

## Remaining Blockers

None.

## Next Recommendation

**Sprint 13 — Execution metrics dashboard**: Expose position sizing data (quantity, notional, risk per trade) in a structured log format consumable by the `logs/trade.log` for post-trade analysis.
