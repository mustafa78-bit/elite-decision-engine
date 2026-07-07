# Sprint 2 Plan

## Sprint Goal

Eliminate the redundant Phase 2 scoring path in `DecisionEngine` and make `DecisionPipeline` the single source of truth for signal evaluation.

## Executive Summary

After Sprint 1, signals flow from `DecisionEngine` → `ExecutionLoop` → `DecisionPipeline` → `TradeEngine` → `Trade(DB)`. However, every signal is scored **twice**: once in `DecisionEngine.process_signal()` (Phase 2) and again in `DecisionPipeline.evaluate()` (Phase 3b). Phase 2 scores are completely discarded — the pipeline re-fetches market data and re-scores from scratch. This doubles latency, wastes API quota, and creates two independent decision paths that can disagree.

## Selected Issue

**Eliminate dual scoring paths.** Remove the Phase 2 `ScoringEngine.score()` call and threshold gating from `DecisionEngine.process_signal()`. Forward raw `Signal` objects directly to `ExecutionLoop.run_once()`, which already handles full evaluation via `DecisionPipeline`.

## Root Cause

`core/engine.py:35`: `scores = self.scorer.score(signal)` fetches OHLCV from Hyperliquid, computes 5 indicators, scores BTC health, checks 3 timeframes for MTF, assesses volatility and risk — **5+ API calls**.

`core/engine.py:54`: `self.execution_loop.run_once(self._build_trade_candidate(...))` passes a `TradeCandidate` to `ExecutionLoop`. At `execution/execution_loop.py:68`, `self.pipeline.evaluate(signal)` is called, which at `execution/pipeline.py:112` calls `self.scoring_engine.score(signal)` — **another 5+ API calls** for the same signal.

Phase 2 scores are stored in a `TradeCandidate` with `confidence=0.0` (hardcoded at `core/engine.py:91`) and discarded by the pipeline. Only the pipeline's scores are used for trade creation.

## Affected Execution Path

```
Signal(DB) → DecisionEngine.run()
  → get_open_signals() → process_signal(signal)
    → [Phase 2] self.scorer.score(signal)          ← 5+ API calls — ELIMINATED
    → [Phase 2] threshold gate (0.55/0.65/0.80)    ← ELIMINATED
    → [Phase 2] _build_trade_candidate(...)         ← ELIMINATED
    → ExecutionLoop.run_once([candidate])
      → process_signal(signal)
        → DecisionPipeline.evaluate(signal)
          → _validate_signal(signal)                ← UNCHANGED
          → _fetch_market_data(signal)              ← UNCHANGED (1 API call)
          → self.scoring_engine.score(signal)       ← UNCHANGED (5+ API calls)
          → self.confidence_engine.calculate(scores)← UNCHANGED
          → return TradeCandidate or None           ← UNCHANGED
        → _create_trade(candidate)                  ← UNCHANGED
        → update_signal_status(...)                 ← UNCHANGED (Sprint 1)
```

## Files That Will Change

| File | Lines | Change |
|------|-------|--------|
| `core/engine.py` | 110 → ~30 | Remove `ScoringEngine` import, `TradeCandidate` import, `self.scorer`, `_build_trade_candidate()`, threshold gating. Simplify `process_signal()` to set `"PROCESSING"` and forward raw `Signal` to `ExecutionLoop.run_once([signal])`. |

## Files That Need NO Changes

| File | Reason |
|------|--------|
| `execution/execution_loop.py` | `run_once()` accepts `Iterable[TradingSignal]`. SQLAlchemy `Signal` ORM has `id`, `symbol`, `side`, `timeframe` — satisfies protocol. `process_signal()` already handles status updates (Sprint 1). No changes. |
| `execution/pipeline.py` | `evaluate()` accepts `TradingSignal` and returns `TradeCandidate` or `None`. No changes. |
| `scoring/scoring_engine.py` | Still called by pipeline. No changes. |
| `database.py` | Status update functions unchanged. No changes. |

## Risk Assessment

| Factor | Rating | Rationale |
|--------|--------|-----------|
| Scope | Low | Single file changed (`core/engine.py`). |
| Regression | Low | Pipeline already handles all validation, scoring, and status updates. No downstream changes. |
| Behavior change | Medium | `WATCH` and `APPROVED`/`STRONG_APPROVE` intermediate statuses no longer set by `DecisionEngine`. The signal goes directly from `PROCESSING` to either `REJECTED` or `EXECUTED`. `WATCH` was an intermediate state with no operational action — no behavior is lost. |
| Rollback | Easy | Single file revert. |
| Verification | Medium | Run `test_pipeline.py` — pipeline decision should be unchanged (`REJECT` with current data). `test_indicators.py` — unchanged. |

## Expected Benefit

| Metric | Before (Sprint 1) | After (Sprint 2) |
|--------|-------------------|-------------------|
| API calls per signal | ~11 (Phase 2 + Phase 3b) | ~5 (Phase 3b only) |
| Lines in `core/engine.py` | 110 | ~30 |
| Decision paths | 2 (can disagree) | 1 (single source of truth) |
| `confidence=0.0` hardcode | Present at `engine.py:91` | Removed |
| Latency per signal | ~10-30s | ~5-15s |

## Estimated Complexity

**Low.** One file, removing dead code and simplifying a single method. No new logic. No interface changes. No new tests required (existing manual tests cover the path).

## Remaining Backlog (after Sprint 2)

| Priority | Issue | Category |
|----------|-------|----------|
| 1 | `TradeCandidate` `id` field | **Done** (Sprint 1) |
| 2 | ConfidenceEngine math bug | **Done** (Sprint 1) |
| 3 | Signal status persistence | **Done** (Sprint 1) |
| 4 | Dual scoring paths | **Sprint 2** |
| 5 | `pandas-ta` missing from `requirements.txt` | **Done** (uncommitted) |
| 6 | `database.py` second `update_signal_status` redefinition overwrites first | Bug |
| 7 | Dead code removal (6 unreferenced files) | Maintainability |
| 8 | Unused dependencies (fastapi, uvicorn, numpy, tenacity, ws, colorlog) | Maintainability |
| 9 | `Trade.signal_id` missing `ForeignKey` constraint | Data integrity |
| 10 | No startup environment validation | Reliability |
| 11 | Dockerfile: no `.dockerignore`, no `USER`, no healthcheck | Operations |
