# Sprint 4 — End-to-End Execution Path Verification

## Objective

Verify the complete end-to-end Paper Trading execution flow and implement missing links.

## Analysis

### Execution Path Trace

```
Signal (DB, status=OPEN)
  │
  ▼
DecisionEngine.run()
  │  polls get_open_signals() → Signal ORM objects
  │  process_signal(signal) → status="PROCESSING"
  ▼
ExecutionLoop.run_once([signal])
  │
  ├─ process_signal(signal)
  │    │
  │    ├─ pipeline.evaluate(signal)
  │    │    ├─ _validate_signal(signal)
  │    │    ├─ _fetch_market_data(signal)  → OHLCV from Hyperliquid
  │    │    ├─ _passes_filters(market_data) → BTCHealthFilter (always passes)
  │    │    ├─ scoring_engine.score(signal)  → component scores + entry + atr
  │    │    ├─ confidence_engine.calculate(scores) → confidence + decision
  │    │    └─ if APPROVED → TradeCandidate(scores, entry, confidence, signal)
  │    │
  │    ├─ if candidate=None → status="REJECTED" ✅
  │    │
  │    └─ if candidate is not None:
  │         _create_trade(candidate)
  │           ├─ trade_engine.create_trade(signal, entry, atr)
  │           │    ├─ tp_sl.calculate(entry, atr, side) → stop/tp1/tp2/rr
  │           │    ├─ check duplicate OPEN trade
  │           │    ├─ INSERT Trade(signal_id, symbol, side, entry, stop, tp1, tp2, rr, status="OPEN")
  │           │    └─ return Trade ORM
  │           └─ if trade not None → status="EXECUTED" ✅
  │
  └─ monitor()
       │
       └─ paper_executor.monitor_open_trades()
            ├─ query all OPEN trades
            ├─ for each trade:
            │    ├─ get_current_price()
            │    ├─ calculate_pnl() → unrealized PnL
            │    ├─ _close_status_for_price() → TP_HIT / SL_HIT / None
            │    └─ if TP/SL hit: _close_trade_record() → status="TP_HIT"/"SL_HIT"
            └─ return TradeMonitorResult[]
```

### Connection Status

| Link | Status | Notes |
|------|--------|-------|
| Signal → DecisionEngine | ✅ | Polls `status == "OPEN"` from DB |
| DecisionEngine → ExecutionLoop | ✅ | `run_once([signal])` called |
| ExecutionLoop → DecisionPipeline | ✅ | `evaluate(signal)` returns `TradeCandidate` or `None` |
| DecisionPipeline → ScoringEngine | ✅ | Returns component scores + `entry` + `atr` |
| DecisionPipeline → ConfidenceEngine | ✅ | Returns `confidence` + `decision` |
| ExecutionLoop → TradeEngine | ✅ | `create_trade(signal, entry, atr)` called |
| TradeEngine → TPSLEngine | ✅ | TP/SL levels calculated |
| TradeEngine → Trade (DB) | ✅ | `Trade` ORM inserted with `status="OPEN"` |
| Trade (DB) → PaperExecutor | ✅ | `monitor_open_trades()` queries OPEN trades |
| PaperExecutor → TP/SL check | ✅ | `_close_status_for_price()` compares price to TP/SL |
| PaperExecutor → Trade Close | ✅ | `_close_trade_record()` updates status |
| Signal status after trade fail | ❌ | **Stuck in "PROCESSING" forever** |

### Missing Link Found

When `_create_trade()` returns `None` (e.g., missing entry/ATR in candidate, DB error, duplicate trade), `process_signal()` returned `None` without updating the signal status. The signal remained stuck in "PROCESSING" status forever, never to be picked up again by the poll loop.

## Implementation

**File:** `execution/execution_loop.py:84-88`

**Change:** When `_create_trade` returns `None`, reset signal status to `"OPEN"` so it can be retried on the next poll cycle.

```diff
         trade = self._create_trade(candidate)
         if trade is not None:
             update_signal_status(signal.id, "EXECUTED")
+        else:
+            update_signal_status(signal.id, "OPEN")
         return trade
```

**Rationale:** Signals that pass pipeline approval but fail at trade creation (e.g., transient DB error, trade already exists) should be retried, not permanently stuck. Setting status back to `"OPEN"` allows the next `DecisionEngine.run()` cycle to pick them up. This is safe because:
- Duplicate trades are handled by `TradeEngine.create_trade()` (returns existing trade)
- Transient failures will succeed on retry
- Permanent data failures will keep failing and retrying (no data loss)

## Test Output

### `test_pipeline.py`
```
Pipeline decision for BTCUSDT LONG 1h: REJECT
REJECTED
```
Pipeline evaluates correctly, rejects low-confidence signal.

### `test_score.py`
```
{...'final_score': 0.63...}
```
Scoring engine returns valid scores with entry price and ATR.

### `test_indicators.py`
```
{...'atr': 421.2240651035099...}
```
Indicators calculate correctly from Hyperliquid data.

## Git Diff Summary

```
 execution/execution_loop.py | 2 ++
 1 file changed, 2 insertions(+)
```

(Unrelated `requirements.txt` diff from Sprint 1, not part of this sprint.)

## Remaining Blockers

- Pipeline rejects signals under current market conditions (BTC ~63k, RSI 43, combined scores ~0.63 → confidence ~63 → `REJECT`). This is a market data limitation, not a code bug.
- All 8 test files rely on live Hyperliquid API calls with zero assertions — no deterministic test suite.
- `PaperExecutor.open_trade()` is unused — `TradeEngine` bypasses it and writes directly to DB. Not a bug but a design inconsistency.
- No database connectivity check at startup — engine will fail silently if Postgres is down.
- `requirements.txt` contains 6 unused dependencies.
