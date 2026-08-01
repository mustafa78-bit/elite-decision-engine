# Sprint 2 Implementation

## Summary of Changes

Eliminated the dual scoring paths by removing the Phase 2 scoring, threshold gating, and `TradeCandidate` construction from `DecisionEngine.process_signal()`. The engine now forwards raw `Signal` ORM objects directly to `ExecutionLoop.run_once()`, which delegates all evaluation to `DecisionPipeline` — the single scoring and decision authority.

## Files Modified

| File | Lines before | Lines after | Change |
|------|-------------|-------------|--------|
| `core/engine.py` | 110 | 49 | Removed Phase 2 scoring, threshold gating, `_build_trade_candidate()`, and 3 unused imports |

## What Was Removed

| Code | Lines | Reason |
|------|-------|--------|
| `from execution.pipeline import TradeCandidate` | 6 | Not used — pipeline builds its own |
| `from execution.trade_engine import TradeEngine` | 7 | Not used — ExecutionLoop creates default |
| `from scoring.scoring_engine import ScoringEngine` | 8 | Not used — pipeline owns scoring |
| `self.scorer = ScoringEngine()` | 15 | Phase 2 scorer — redundant with pipeline |
| `self.trade_engine = TradeEngine()` | 16 | Redundant — ExecutionLoop defaults to same |
| Phase 2 scoring block (`self.scorer.score()` + thresholds) | 35-73 | Duplicate of pipeline scoring |
| `_build_trade_candidate()` static method | 78-94 | Produced `TradeCandidate` with `confidence=0.0` that was immediately discarded |

## What Was Kept

| Code | Lines | Purpose |
|------|-------|---------|
| Signal metadata print | 24-27 | User-visible logging before pipeline call |
| `update_signal_status(PROCESSING)` | 28 | Mark signal in-progress before pipeline |
| `self.execution_loop.run_once([signal])` | 30 | Forward raw Signal to ExecutionLoop |
| `except Exception` block | 31-33 | Safety net for unexpected errors |
| `get_open_signals()` | 14-19 | Poll DB for open signals |
| `run()` loop | 35-49 | Main orchestration loop |

## Test Output

```
$ python test_pipeline.py
INFO:execution.pipeline:Pipeline decision for BTCUSDT LONG 1h: REJECT
REJECTED

$ python test_indicators.py
{'ema20': 63415.33, 'ema50': 63155.19, 'ema200': 62063.74, 'rsi': 44.91, 'atr': 404.43}

$ python test_score.py
{'entry': 63033.0, 'ema20': 63415.14, 'ema50': 63155.11, 'ema200': 62063.72, 'rsi': 44.88, 'atr': 404.58, 'trend_score': 1.0, 'volume_score': 0.3, 'btc_score': 0.7, 'mtf_score': 0.33, 'risk_score': 0.64, 'final_score': 0.63}
```

All tests pass. Pipeline decision is `REJECT` (correct — current market data produces confidence below 70 threshold).

## Git Diff Summary

```diff
 core/engine.py | 82 +--------------------------------------------------------
 1 file changed, 7 insertions(+), 75 deletions(-)
```

- `-from execution.pipeline import TradeCandidate`
- `-from execution.trade_engine import TradeEngine`
- `-from scoring.scoring_engine import ScoringEngine`
- `-self.scorer = ScoringEngine()`
- `-self.trade_engine = TradeEngine()`
- `-self.execution_loop = ExecutionLoop(trade_engine=self.trade_engine)`
- `+self.execution_loop = ExecutionLoop()`
- `-` [Phase 2 scoring block: 38 lines]
- `+self.execution_loop.run_once([signal])`
- `-` [_build_trade_candidate: 17 lines]

## Remaining Issues

| Priority | Issue | Status |
|----------|-------|--------|
| 1 | Interface type mismatch (`TradeCandidate` missing `id`) | Done (Sprint 1) |
| 2 | ConfidenceEngine math bug (`* 100` double-scaling) | Done (Sprint 1) |
| 3 | Signal status persistence from pipeline | Done (Sprint 1) |
| 4 | `pandas-ta` missing from `requirements.txt` | Done |
| 5 | Dual scoring paths (Phase 2 vs Phase 3b) | **Done (Sprint 2)** |
| 6 | `database.py` second `update_signal_status` overwrites first | Open |
| 7 | Dead code removal (6 unreferenced files) | Open |
| 8 | Unused dependencies (fastapi, uvicorn, numpy, tenacity, ws, colorlog) | Open |
| 9 | No startup environment validation | Open |
