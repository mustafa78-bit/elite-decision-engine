# Sprint 2 Review — Phase 2 Scoring Removal Proof

## Current Responsibilities (DecisionEngine, `core/engine.py`)

| ID | Responsibility | Lines | Implementation |
|----|---------------|-------|----------------|
| R1 | Print signal metadata (symbol, side, timeframe) | 29-32 | `print(f"Coin: {signal.symbol}")` |
| R2 | Set DB status to `"PROCESSING"` | 33 | `update_signal_status(signal.id, "PROCESSING")` |
| R3 | Fetch market data and compute indicators (5+ API calls) | 35 | `self.scorer.score(signal)` → ScoringEngine |
| R4 | Compute trend, volume, BTC, MTF, risk scores | 35 | ScoringEngine internals |
| R5 | Compute weighted `final_score` | 36 | `scores["final_score"]` (0.30/0.20/0.20/0.20/0.10) |
| R6 | Print `final_score` | 38 | `print("SCORE:", score)` |
| R7 | Gate: `score < 0.55` → status `"REJECTED"`, return | 40-43 | Early exit, no pipeline call |
| R8 | Gate: `0.55 ≤ score < 0.65` → status `"WATCH"`, return | 45-48 | Early exit, no pipeline call |
| R9 | Gate: `0.65 ≤ score < 0.80` → status `"APPROVED"` | 50-62 | Calls ExecutionLoop |
| R10 | Gate: `score ≥ 0.80` → status `"STRONG_APPROVE"` | 64-73 | Calls ExecutionLoop |
| R11 | Build `TradeCandidate` with `confidence=0.0` | 78-94 | `_build_trade_candidate()` |
| R12 | Catch all exceptions → status `"REJECTED"` | 74-76 | Safety net |
| R13 | Poll DB for `Signal.status == "OPEN"` | 100 | `get_open_signals()` |
| R14 | Sleep `CHECK_INTERVAL` seconds between cycles | 110 | `time.sleep(CHECK_INTERVAL)` |

## Future Responsibilities (After Sprint 2)

| ID | Fate | New owner | Location |
|----|------|-----------|----------|
| R1 | **Remain** | DecisionEngine | `core/engine.py` — `process_signal()` |
| R2 | **Remain** | DecisionEngine | `core/engine.py` — `process_signal()` |
| R3 | **Remove** | n/a | Duplicate of pipeline's own scoring |
| R4 | **Remove** | n/a | Duplicate of pipeline's own scoring |
| R5 | **Remove** | n/a | Duplicate of pipeline's own confidence |
| R6 | **Remove** | n/a | Pipeline logs decision instead |
| R7 | **Move** | ExecutionLoop:75 | Pipeline returns None → ExecutionLoop sets `"REJECTED"` |
| R8 | **Remove** | n/a | `"WATCH"` has no downstream consumer |
| R9 | **Move** | DecisionPipeline:112-124 | Pipeline scores and thresholds via ConfidenceEngine |
| R10 | **Move** | DecisionPipeline:112-124 | Pipeline scores and thresholds via ConfidenceEngine |
| R11 | **Remove** | n/a | Pipeline builds its own TradeCandidate (pipeline.py:127-137) |
| R12 | **Remain** | DecisionEngine | `core/engine.py` — `process_signal()` `except` block |
| R13 | **Remain** | DecisionEngine | `core/engine.py` — `get_open_signals()` |
| R14 | **Remain** | DecisionEngine | `core/engine.py` — `run()` |

## Responsibility Mapping

### Items Removed (R3, R4, R5, R6, R8, R11)

| Removed | Why it is safe to remove |
|---------|--------------------------|
| **R3-R5** (Phase 2 scoring + `final_score`) | `DecisionPipeline.evaluate()` at `execution/pipeline.py:112` already calls `self.scoring_engine.score(signal)` with the **same** ScoringEngine. The pipeline then runs ConfidenceEngine to produce a decision. Phase 2's scores are computed, stored in a `TradeCandidate` with `confidence=0.0`, and immediately discarded by the pipeline which re-scores from scratch. Removing Phase 2 scoring eliminates 5+ redundant API calls while producing the exact same result — the pipeline's decision. |
| **R6** (print SCORE) | The pipeline logs the decision at `pipeline.py:116-122`. The intermediate `final_score` print is redundant — the decision already reflects the score. |
| **R8** (WATCH gate) | `"WATCH"` is set at `engine.py:46` but **never queried or acted upon** anywhere in the codebase. `get_open_signals()` filters for `status == "OPEN"`. `monitor_open_trades()` filters for `Trade.status == "OPEN"`. No SQL query, no state machine, no consumer reads `"WATCH"`. Removing it loses no business logic. |
| **R11** (`_build_trade_candidate`) | `DecisionPipeline.evaluate()` at `pipeline.py:127-137` already builds the canonical `TradeCandidate` with correct scores from its own scoring pass. The engine's `_build_trade_candidate()` produces a candidate with `confidence=0.0` that is never used — the pipeline ignores it and builds its own. |

### Items Moved (R7, R9, R10)

| Moved | New location | How it is covered |
|-------|-------------|-------------------|
| **R7, R9, R10** (threshold gating: REJECTED, APPROVED, STRONG_APPROVE) | `DecisionPipeline.evaluate()` lines 112-124 + `ExecutionLoop.process_signal()` lines 68-86 | The pipeline's `ConfidenceEngine` evaluates the signal and returns a decision (`"REJECT"`, `"WATCH"`, `"APPROVE"`, or `"STRONG_APPROVE"`). The pipeline then checks `APPROVED_DECISIONS` at line 124. If not approved, pipeline returns `None`. `ExecutionLoop.process_signal()` at line 75 calls `update_signal_status(signal.id, "REJECTED")`. If approved, a `TradeCandidate` is returned, a trade is created, and `update_signal_status(signal.id, "EXECUTED")` is called at line 86. |

### Items Remaining (R1, R2, R12, R13, R14)

These form the simplified `DecisionEngine`:
- Set status to `PROCESSING`
- Forward signal to `ExecutionLoop.run_once([signal])`
- Catch any unexpected exception and set `REJECTED`
- Poll DB and sleep between cycles

## Execution Path Comparison

### Before Sprint 2

```
DecisionEngine.run()
  → get_open_signals()                     [R13]
  → process_signal(signal)
    → print metadata                       [R1]
    → update_signal_status(PROCESSING)      [R2]
    → scores = self.scorer.score(signal)    [R3, R4, R5]  ← 5+ API calls
    → final_score = scores["final_score"]   [R5]
    → print SCORE                          [R6]
    → if < 0.55: REJECTED + return         [R7]
    → if < 0.65: WATCH + return            [R8]
    → if < 0.80: APPROVED                  [R9]
      → _build_trade_candidate(...)         [R11]  ← confidence=0.0
      → ExecutionLoop.run_once([candidate])
        → DecisionPipeline.evaluate(signal)
          → _validate_signal(signal)
          → _fetch_market_data(signal)      ← 1 API call
          → self.scoring_engine.score(signal)  ← 5+ API calls (DUPLICATE)
          → self.confidence_engine.calculate(scores)
          → return TradeCandidate or None
        → _create_trade(candidate)
        → update_signal_status(REJECTED|EXECUTED)
    → if ≥ 0.80: STRONG_APPROVE            [R10]
      → _build_trade_candidate(...)         [R11]  ← confidence=0.0
      → ExecutionLoop.run_once([candidate])  ← DUPLICATE with above
  → time.sleep(CHECK_INTERVAL)             [R14]
```

### After Sprint 2

```
DecisionEngine.run()
  → get_open_signals()                     [R13]
  → process_signal(signal)
    → print metadata                       [R1]
    → update_signal_status(PROCESSING)      [R2]
    → ExecutionLoop.run_once([signal])       ← raw Signal ORM
      → process_signal(signal)
        → DecisionPipeline.evaluate(signal)
          → _validate_signal(signal)
          → _fetch_market_data(signal)      ← 1 API call
          → self.scoring_engine.score(signal)  ← 5+ API calls (SINGLE PASS)
          → self.confidence_engine.calculate(scores)
          → return TradeCandidate or None
        → if None: update_signal_status(REJECTED)
        → if TradeCandidate: _create_trade(candidate)
          → update_signal_status(EXECUTED)
  → time.sleep(CHECK_INTERVAL)             [R14]
```

**Key differences:**
- Phase 2 scoring (R3-R5) eliminated — 5+ API calls saved
- `_build_trade_candidate` (R11) eliminated — `confidence=0.0` dead code removed
- `WATCH` status (R8) eliminated — was write-only
- Raw `Signal` ORM passed to `ExecutionLoop.run_once()` instead of hand-built `TradeCandidate`
- Pipeline remains the single scoring and decision authority

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Exception in `ExecutionLoop.run_once()` not caught | Low | Medium | `DecisionEngine.process_signal()` retains its `except Exception` block (R12) — any exception from ExecutionLoop is caught and sets `REJECTED` |
| `Signal` ORM does not satisfy `TradingSignal` protocol | None | Critical | Verified: `Signal` has `id` (Integer PK), `symbol` (String), `side` (String), `timeframe` (String) — exact fields required by `TradingSignal` protocol at `pipeline.py:24-30`. Already tested — `test_pipeline.py` passes `ExampleSignal` with same fields. |
| Pipeline thresholds reject signals that Phase 2 would have approved | Certain | Low | This is the **intended behavior change**. Phase 2 thresholds (0.55/0.80) and pipeline thresholds (70/80/90) were never aligned. Pipeline is the designated decision maker. |
| `WATCH` signals now get `REJECTED` | Certain | Low | `WATCH` had no consumer. Setting `REJECTED` is more accurate — the signal was evaluated and not approved. |
| `run_once()` called with single-element list instead of a batch | No change | None | Already the current behavior — `process_signal()` already calls `run_once()` with `[self._build_trade_candidate(...)]` — a single-element list. Replacing with `[signal]` changes element type but not count. |

## Regression Risk

| Area | Risk Level | Reason |
|------|-----------|--------|
| Pipeline evaluation | None | `test_pipeline.py` calls `DecisionPipeline.evaluate()` directly — no code path changes in pipeline |
| Trade creation | None | `TradeEngine.create_trade()` receives `TradeCandidate.signal` (original Signal ORM) — unchanged |
| Status persistence | None | `ExecutionLoop.update_signal_status()` calls in Sprint 1 are unchanged |
| Paper monitoring | None | `PaperExecutor.monitor_open_trades()` runs inside `run_once()` — unchanged |
| DB schema | None | No model changes. Status values used (`PROCESSING`, `REJECTED`, `EXECUTED`) are all existing strings |
| Existing tests | None | All 8 test files test individual components (pipeline, scoring, indicators, etc.) directly — none depend on `DecisionEngine.process_signal()` |

## Final Recommendation

**Approved for Sprint 2 implementation.**

The Phase 2 scoring path provides zero unique business logic. Every decision it makes is duplicated by `DecisionPipeline`, which is the designated decision authority. Removing Phase 2 scoring:

- Saves 5+ API calls per signal (50% reduction)
- Eliminates 80 lines of dead/redundant code from `core/engine.py`
- Removes the `confidence=0.0` hardcode artifact
- Removes the write-only `WATCH` status
- Makes the pipeline the single consistent decision path

No test needs to change. No downstream component needs to change. The `Signal` ORM already satisfies the `TradingSignal` protocol consumed by `ExecutionLoop.run_once()`.
