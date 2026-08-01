# Sprint 2 — Missing Dependency Fix

## Plan

Add `pandas-ta` to `requirements.txt`.

**Why:** `pandas_ta` is imported by `market_data/indicators.py:1` but was absent from `requirements.txt`. A fresh `pip install -r requirements.txt` produces an environment that crashes with `ModuleNotFoundError` on the first indicator calculation. Every scoring path depends on `IndicatorEngine.calculate()`: `ScoringEngine`, `BTCHealth`, `MTFEngine`, `VolatilityEngine`.

## Implementation

**File:** `requirements.txt`

**Change:** Added `pandas-ta` on the last line.

```diff
+ pandas-ta
```

No other files needed changes.

## Test output

```
$ python test_indicators.py
{'ema20': 63454.70, 'ema50': 63159.82, 'ema200': 62053.45, 'rsi': 45.77, 'atr': 428.16}

$ python test_pipeline.py
INFO:execution.pipeline:Pipeline decision for BTCUSDT LONG 1h: REJECT
REJECTED
```

Both tests pass. Indicator values are non-zero and valid. Pipeline decision is `REJECT` (correct — ATR data is real but the `ATRr_14` column name is not a bug; see Sprint 2 verification).

## Git diff summary

```diff
diff --git a/requirements.txt b/requirements.txt
index 34cfdef..8dd46a4 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -8,4 +8,5 @@ pandas
 numpy
 tenacity
 websocket-client
-colorlog
\ No newline at end of file
+colorlog
+pandas-ta
```

One file changed, one line added.

## Remaining issues

| Priority | Issue | Status |
|----------|-------|--------|
| 1 | Interface type mismatch (`TradeCandidate` missing `id`) | Done (Sprint 1) |
| 2 | ConfidenceEngine math bug (`* 100` double-scaling) | Done (Sprint 1) |
| 3 | Signal status persistence from pipeline | Done (Sprint 1) |
| 4 | `ATRr_14` column name | **Not a bug** (verified Sprint 2) |
| 5 | `pandas-ta` missing from `requirements.txt` | **Done (Sprint 2)** |
| 6 | Duplicate market data fetching (6 API calls per eval) | Open |
| 7 | Dual scoring paths (Phase 2 vs Phase 3b) | Open |
| 8 | Dead code removal | Open |
| 9 | Startup validation | Open |
