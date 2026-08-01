# Sprint 5 — End-to-End Integration Test

## Objective

Create the first complete end-to-end Paper Trading integration test verifying:

```
Signal -> DecisionEngine -> ExecutionLoop -> DecisionPipeline
-> TradeEngine -> Trade(DB) -> PaperExecutor -> TP/SL -> Trade Close
```

## Analysis

The existing architecture already supports dependency injection through `ExecutionLoop.__init__`, `DecisionPipeline.__init__`, and `PaperExecutor.__init__`. Two gaps were identified:

1. **DecisionEngine** (`core/engine.py:10`) did not accept injection for its `ExecutionLoop`. It always created `self.execution_loop = ExecutionLoop()` with real components. An optional `execution_loop` parameter was needed to inject mocked dependencies.

2. **No integration test existed** — all 8 existing test files make real Hyperliquid API calls with zero assertions. No file validates the end-to-end path.

## Implementation

### 1. `core/engine.py` — Injection hook (2 lines changed)

```diff
-    def __init__(self):
+    def __init__(self, execution_loop=None):
         print("Decision Engine initialized")
-        self.execution_loop = ExecutionLoop()
+        self.execution_loop = execution_loop or ExecutionLoop()
```

Backward-compatible: `DecisionEngine()` creates the same `ExecutionLoop()` as before.

### 2. New file: `test_integration.py` — End-to-end test

Six phases with assertions:

| Phase | What it tests | Assertions |
|-------|---------------|------------|
| 1 | Insert test Signal in DB | `signal.id` is set |
| 2 | Build pipeline with mock scorer/collector | — |
| 3 | Process signal through DecisionEngine | — |
| 4 | Trade created in DB | `status=OPEN`, correct entry/stop/tp1/rr, signal `EXECUTED` |
| 5 | Monitor with price above TP1 | Trade found in results, `status=TP_HIT` |
| 6 | Trade closed in DB | `status=TP_HIT`, `exit_price=52000`, `close_reason=TP_HIT` |

**Mock components:**

- `MockCollector`: Returns constant `close` price in a DataFrame. Dual use: entry-match price (50000) during trade creation, above-TP price (52000) during monitor close.
- `MockScoringEngine`: Returns hardcoded scores producing `confidence=90` → `STRONG_APPROVE`. All scores = 1.0 except `risk_score=0.0`.
- `ConfidenceEngine`: Real — validates the pipeline's decision gate is working.
- `TradeEngine` / `TPSLEngine`: Real — validates TP/SL calculation and DB persistence.
- Empty `filters=()` tuple: Skips the always-passing `BTCHealthFilter`.

**TP/SL mechanics verified:**
- LONG entry=50000, ATR=500
- stop = 50000 - 500*1.5 = 49250
- tp1 = 50000 + 500*2.0 = 51000
- Monitor at 52000 → 52000 >= 51000 → TP_HIT

## Test Output

### New integration test
```
[SIGNAL] Created test signal id=1381
[TRADE] Created id=5 entry=50000.0 stop=49250.0 tp1=51000.0 rr=1.33
[MONITOR] Trade id=5 status=TP_HIT
[CLOSE] Trade id=5 status=TP_HIT exit=52000.0 reason=TP_HIT
=== ALL INTEGRATION TESTS PASSED ===
```

### Existing test suite (all pass)
| Test | Result |
|------|--------|
| `test_pipeline.py` | Pipeline decision: REJECT |
| `test_score.py` | Scores returned |
| `test_indicators.py` | Indicators calculated |
| `test_btc.py` | BTC score: 0.7 |
| `test_collector.py` | OHLCV fetched |
| `test_mtf.py` | MTF scores: LONG 0.33 |
| `test_volatility.py` | Volatility: 0.6 |
| `test_volume.py` | Volume ratio: 0.3 |

## Git Diff Summary

```
 core/engine.py     | 4 ++--
 test_integration.py | 1 file (new, 105 lines)
 2 files changed, 2 insertions(+), 2 deletions(-)
```

(Unrelated `requirements.txt` diff from Sprint 1.)

## Remaining Blockers

- **Dual scoring paths not fully removed**: The `ScoringEngine` makes real Hyperliquid API calls even when mocked — the mock bypasses it entirely via injection.
- **No test database**: The integration test writes to and cleans up from the shared Postgres database. Test isolation requires a dedicated test DB.
- **Async/real-time monitoring edge cases**: `PaperExecutor.monitor_open_trades()` calls `get_current_price()` synchronously for each trade. With many open trades, this could be slow.
- **No CI/CD**: Tests must be run manually.

## Next Recommendation

- Add a dedicated test database with `TEST_DATABASE_URL` env configuration.
- Extract common mocks (MockCollector, MockScoringEngine) into a shared `tests/conftest.py` or `tests/mocks.py`.
- Convert all 8 existing test files to use deterministic mock data with assertions.
