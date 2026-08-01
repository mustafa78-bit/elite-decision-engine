# Production Readiness Review — Elite Decision Engine

## Methodology

Every file in the repository was read in full. All conclusions are derived exclusively from the source code present. No assumptions are made about external systems, uncommitted changes, or intended behavior not expressed in the code. Virtual environments, cache directories, and Git metadata are excluded.

---

## Execution Flow Trace

### Phase 0: Signal Generation

| Attribute | Detail |
|-----------|--------|
| **File** | `signal_generator.py` |
| **Class** | None |
| **Function** | `create_signal()` |
| **Input** | None |
| **Output** | SQLAlchemy `Signal` ORM inserted into `signals` table |
| **Side effects** | INSERT with random symbol (`BTCUSDT`/`ETHUSDT`/`SOLUSDT`), random side, `status="OPEN"` |
| **Dependencies** | `get_session()`, `Signal` model |
| **Error handling** | None |
| **Implementation status** | **Dead Code** — runs only as `python signal_generator.py`, never imported |

This phase is disconnected from the rest of the system. `DecisionEngine.run()` independently polls the `signals` table for `status == "OPEN"`. There is no import, no function call, no shared configuration between the generator and the consumer — they are independent processes that share only the database schema.

---

### Phase 1: Entry — `app.py` → `DecisionEngine.run()`

**1a. `app.py::main()`**

| Attribute | Detail |
|-----------|--------|
| **File** | `app.py:5-13` |
| **Class** | None |
| **Function** | `main()` |
| **Input** | None |
| **Output** | None |
| **Side effects** | Calls `create_tables()` (idempotent schema creation), prints startup message, enters infinite loop |
| **Dependencies** | `database.create_tables`, `core.engine.DecisionEngine` |
| **Error handling** | None — any exception propagates to the interpreter, process terminates |
| **Implementation status** | **Complete** |

**1b. `DecisionEngine.__init__()`**

| Attribute | Detail |
|-----------|--------|
| **File** | `core/engine.py:13-17` |
| **Class** | `DecisionEngine` |
| **Function** | `__init__()` |
| **Input** | None |
| **Output** | None |
| **Side effects** | Instantiates `ScoringEngine()`, `TradeEngine()`, `ExecutionLoop(trade_engine=self.trade_engine)` |
| **Dependencies** | `ScoringEngine`, `TradeEngine`, `ExecutionLoop` |
| **Error handling** | None |
| **Implementation status** | **Complete** |

Note that `ExecutionLoop` receives only `trade_engine`. The `pipeline` and `paper_executor` parameters are not provided, so both default to fresh instances. There is no shared pipeline, no shared collector, no shared configuration.

**1c. `DecisionEngine.run()`**

| Attribute | Detail |
|-----------|--------|
| **File** | `core/engine.py:95-109` |
| **Class** | `DecisionEngine` |
| **Function** | `run()` |
| **Input** | None |
| **Output** | None |
| **Side effects** | Every `CHECK_INTERVAL` (10 seconds), queries DB for `Signal.status == "OPEN"`, calls `process_signal()` for each |
| **Dependencies** | `get_session()`, `Signal` model, `CHECK_INTERVAL` from `config.py` |
| **Error handling** | **None** — DB connection failure, network error, any exception terminates the process immediately |
| **Implementation status** | **Complete** |

---

### Phase 2: Signal Evaluation — `DecisionEngine.process_signal()`

| Attribute | Detail |
|-----------|--------|
| **File** | `core/engine.py:26-76` |
| **Class** | `DecisionEngine` |
| **Function** | `process_signal(signal)` |
| **Input** | SQLAlchemy `Signal` ORM object (has `id`, `symbol`, `side`, `timeframe`, `price`, `status`) |
| **Output** | None |
| **Side effects** | DB status updates: `"PROCESSING"`, then one of `"REJECTED"`, `"WATCH"`, `"APPROVED"`, `"STRONG_APPROVE"` |
| **Dependencies** | `update_signal_status`, `ScoringEngine.score()`, `ExecutionLoop.run_once()`, `TradeCandidate` |
| **Error handling** | Catches `Exception`, prints `"ERROR: {e}"`, sets DB status to `"REJECTED"` |
| **Implementation status** | **Complete** |

**Detailed execution:**

1. `update_signal_status(signal.id, "PROCESSING")` — DB write
2. `self.scorer.score(signal)` → `ScoringEngine.score()`:
   - Strips `"USDT"` from `signal.symbol` (e.g. `"BTCUSDT"` → `"BTC"`)
   - Fetches OHLCV from Hyperliquid via `HyperliquidCollector.get_ohlcv()`
   - `IndicatorEngine.calculate(df)` → `{ema20, ema50, ema200, rsi, atr}`
   - `VolumeEngine.score(df)` → `{current_volume, average_volume, ratio, score}`
   - `BTCHealth.score()` → float (0.0–1.0) — **separate API call internally**
   - `VolatilityEngine.score(values)` → `{volatility, score}`
   - `MTFEngine.score(symbol, side)` → float (0.0–1.0) — **3 API calls internally** (15m, 1h, 4h)
   - `RiskEngine.score(values, volatility)` → float (0.0–1.0)
   - Computes `final_score = trend*0.30 + volume*0.20 + btc*0.20 + mtf*0.20 + risk*0.10`
   - Returns dict with 13 keys: `entry`, `ema20`, `ema50`, `ema200`, `rsi`, `atr`, `trend_score`, `volume_score`, `btc_score`, `mtf_score`, `risk_score`, `final_score`
3. Threshold branch on `final_score`:
   - `< 0.55` → status `"REJECTED"`, return
   - `< 0.65` → status `"WATCH"`, return
   - `< 0.80` → status `"APPROVED"`, proceed to Phase 3
   - `>= 0.80` → status `"STRONG_APPROVE"`, proceed to Phase 3
4. For approved signals: `_build_trade_candidate(signal, scores, decision)` → `TradeCandidate`

**Data entering Phase 3:**

```
TradeCandidate(
    symbol=signal.symbol,         # "BTCUSDT"
    side=signal.side,             # "LONG"
    timeframe=signal.timeframe,   # "1h"
    entry=scores["entry"],        # latest close price
    scores=scores,                # full scores dict from ScoringEngine
    confidence=0.0,               # HARDCODED — never calculated
    decision="APPROVED"/"STRONG_APPROVE",
    signal=signal,                # original SQLAlchemy Signal ORM object
)
```

**Critical finding at `core/engine.py:90`:** `confidence` is hardcoded to `0.0`. The scores from `ScoringEngine` contain detailed component scores, but the `ConfidenceEngine` is never consulted here.

**Critical finding at `core/engine.py:91`:** The decision string is `"APPROVED"` (with trailing D). This differs from what `DecisionPipeline` produces (`"APPROVE"` without D) and from what `APPROVED_DECISIONS` checks at `pipeline.py:21`.

---

### Phase 3: Orchestration — `ExecutionLoop.run_once()` — **PARTIAL (was COMPLETE BREAK)**

| Attribute | Detail |
|-----------|--------|
| **File** | `execution/execution_loop.py:44-62` |
| **Class** | `ExecutionLoop` |
| **Function** | `run_once(signals: Iterable[TradingSignal])` |
| **Input** | `[TradeCandidate]` — single-element list passed from `process_signal()` |
| **Output** | `ExecutionLoopResult` |
| **Side effects** | `update_signal_status(signal.id, "REJECTED")` on pipeline rejection; `update_signal_status(signal.id, "EXECUTED")` on trade creation |
| **Dependencies** | `DecisionPipeline`, `TradeEngine`, `PaperExecutor`, `update_signal_status` |
| **Error handling** | None at this level |
| **Implementation status** | **Partial** — orchestration logic is structurally valid; interface break resolved; signal status now persisted |

**Original break (now resolved):**

`TradeCandidate` was missing the `id` field required by `_validate_signal()`. Adding `id: int` to the `TradeCandidate` dataclass and populating it at both construction sites (`DecisionEngine._build_trade_candidate()` at `core/engine.py:85` and `DecisionPipeline.evaluate()` at `execution/pipeline.py:128`) allows validation to pass and the pipeline to return a `TradeCandidate` instead of `None`.

**Updated call chain:**

| # | Call | File:Line | What happens |
|---|------|-----------|--------------|
| 1 | `run_once([trade_candidate])` | `execution_loop.py:45` | Iterates over `[TradeCandidate]` |
| 2 | `process_signal(signal)` | `execution_loop.py:65` | `signal` = `TradeCandidate` (now has `id`) |
| 3 | `self.pipeline.evaluate(signal)` | `execution_loop.py:68` | Calls into `DecisionPipeline` |
| 4 | `_validate_signal(signal)` | `pipeline.py:100` → `220-227` | Checks `"id"`, `"symbol"`, `"side"`, `"timeframe"` — all present |
| 5 | Validation passes | `pipeline.py:227` | No exception raised |
| 6 | Pipeline scores, gets confidence | `pipeline.py:101-112` | Independent scoring from Hyperliquid |
| 7 | Pipeline returns `TradeCandidate` | `pipeline.py:127` | Frozen candidate with `id`, scores, decision |
| 8 | Pipeline rejects (confidence low) | `pipeline.py:75` | `update_signal_status(signal.id, "REJECTED")` |
| 9 | Pipeline approves → trade created | `execution_loop.py:84-86` | `update_signal_status(signal.id, "EXECUTED")` |

---

### Phase 3b: (Intended Path) — `DecisionPipeline.evaluate()`

| Attribute | Detail |
|-----------|--------|
| **File** | `execution/pipeline.py:96-139` |
| **Class** | `DecisionPipeline` |
| **Function** | `evaluate(signal: TradingSignal)` |
| **Input** | `TradingSignal`-conforming object (requires: `id`, `symbol`, `side`, `timeframe`) |
| **Output** | `TradeCandidate` or `None` |
| **Dependencies** | `HyperliquidCollector`, `BTCHealthFilter`, `ScoringEngine`, `ConfidenceEngine` |
| **Error handling** | `except Exception` at line 137 — catches all, logs, returns `None` |
| **Implementation status** | **Partial** — structurally sound but unreachable from Phase 2, and contains independent bugs |

**Sub-phases:**

| # | Step | Lines | Entry Data | Exit Data | Status |
|---|------|-------|------------|-----------|--------|
| 3b-i | `_validate_signal(signal)` | 100, 220-227 | TradingSignal | None or ValueError | Complete |
| 3b-ii | `_fetch_market_data(signal)` | 101, 146-158 | symbol, timeframe | pandas DataFrame | Complete |
| 3b-iii | `_passes_filters(market_data)` | 107-109, 160-170 | DataFrame | `True` (always) | **Stub** |
| 3b-iv | `self.scoring_engine.score(signal)` | 111 | TradingSignal | scores dict | Complete (duplicated) |
| 3b-v | `self.confidence_engine.calculate(scores)` | 112 | scores dict | `{confidence, decision}` | **Bugged** |
| 3b-vi | Decision gate | 123-124 | decision string | passes if in `{"APPROVE", "STRONG_APPROVE"}` | Complete |
| 3b-vii | Return TradeCandidate | 126-135 | scores, decision | frozen TradeCandidate | Complete |

**Step 3b-iii:** `_fetch_market_data()` at line 146-158 fetches OHLCV data used ONLY by the filters. Then `ScoringEngine.score()` at line 111 fetches the **same data again** from Hyperliquid. Two HTTP requests for data consumed only by a no-op placeholder.

**Step 3b-v — ConfidenceEngine math bug at `core/confidence_engine.py:11-19`:**

```python
confidence = (
    score["trend_score"] * 30 +     # input 0-1 → product 0-30
    score["volume_score"] * 20 +    # input 0-1 → product 0-20
    score["btc_score"] * 20 +       # input 0-1 → product 0-20
    score["mtf_score"] * 20 +       # input 0-1 → product 0-20
    score["risk_score"] * 10        # input 0-1 → product 0-10
)                                   # sum range: 0 to 100

confidence = max(0, min(100, confidence * 100))  # line 19
```

All component scores are in range **0.0–1.0**. The weighted sum produces **0–100**. Then `confidence * 100` produces **0–10000**. Clamped to 100.

**Result:** Every non-trivial input produces `confidence = 100`, which triggers `decision = "STRONG_APPROVE"`. The decision gate is mathematically dead.

**Demonstration with realistic values:** `trend=1.0, volume=0.5, btc=0.7, mtf=0.5, risk=0.8` → weighted sum = `30+10+14+10+8 = 72` → `72 * 100 = 7200` → clamped to `100` → `"STRONG_APPROVE"`.

**Step 3b-vi — Decision string mismatch:** `ConfidenceEngine` produces `"APPROVE"` (no D). `APPROVED_DECISIONS` at `pipeline.py:21` = `frozenset({"APPROVE", "STRONG_APPROVE"})`. This matches. However, if a `TradeCandidate` from `DecisionEngine` (which uses `"APPROVED"` with D) ever reached this gate, it would be rejected because `"APPROVED" ≠ "APPROVE"`.

---

### Phase 4: Trade Creation — `ExecutionLoop._create_trade()` → `TradeEngine`

**4a. `ExecutionLoop._create_trade()`**

| Attribute | Detail |
|-----------|--------|
| **File** | `execution/execution_loop.py:91-118` |
| **Class** | `ExecutionLoop` |
| **Function** | `_create_trade(candidate: TradeCandidate)` |
| **Input** | `TradeCandidate` (unreachable due to Phase 3 break) |
| **Output** | SQLAlchemy `Trade` object or `None` |
| **Side effects** | DB INSERT, logging |
| **Dependencies** | `TradeEngine`, `TradeCandidate` |
| **Error handling** | None |
| **Implementation status** | **Complete** (but unreachable) |

Extracts `entry = candidate.entry` and `atr = candidate.scores.get("atr")`. Returns `None` if either is missing. Calls `self.trade_engine.create_trade(signal=candidate.signal, entry=float(entry), atr=float(atr))`.

**4b. `TradeEngine.create_trade()`**

| Attribute | Detail |
|-----------|--------|
| **File** | `execution/trade_engine.py:10-64` |
| **Class** | `TradeEngine` |
| **Function** | `create_trade(signal, entry, atr)` |
| **Input** | Signal (TradingSignal-compatible), entry (float), atr (float) |
| **Output** | SQLAlchemy `Trade` object or `None` |
| **Side effects** | DB INSERT into `trades` table |
| **Dependencies** | `TPSLEngine`, `Trade` model, `get_session()` |
| **Error handling** | Catches `Exception` on DB operations, prints `"TRADE CREATE ERROR: {e}"`, rolls back, returns `None`; duplicate detection via signal_id query |
| **Implementation status** | **Complete** |

**Sub-steps:**

1. `self.tp_sl.calculate(entry=entry, atr=atr, side=signal.side)` → levels dict
2. Opens DB session
3. Queries `Trade` for `signal_id == signal.id AND status == "OPEN"`
4. If duplicate found: prints, returns existing
5. Otherwise: `Trade(signal_id, symbol, side, entry, stop, tp1, tp2, rr, status="OPEN")` → INSERT → commit → return

**Uses `print()` at line 34** instead of logging.

---

### Phase 4a: TP/SL Calculation — `TPSLEngine.calculate()`

| Attribute | Detail |
|-----------|--------|
| **File** | `execution/tp_sl.py:3-36` |
| **Class** | `TPSLEngine` |
| **Function** | `calculate(entry, atr, side)` |
| **Input** | entry (float), atr (float), side (str) |
| **Output** | Dict: `{entry, stop, tp1, tp2, rr}` |
| **Dependencies** | None |
| **Error handling** | None |
| **Implementation status** | **Complete** |

```python
LONG:   stop = entry - ATR*1.5,   tp1 = entry + ATR*2.0,   tp2 = entry + ATR*4.0
SHORT:  stop = entry + ATR*1.5,   tp1 = entry - ATR*2.0,   tp2 = entry - ATR*4.0
R:R = (ATR*2.0) / (ATR*1.5) = 1.33  # CONSTANT
```

Fallback: if `atr <= 0`, use `atr = entry * 0.01` (1% of entry price).

**The R:R ratio is always 1.33 regardless of market structure, volatility regime, or any price-level analysis.**

---

### Phase 5: Database Persistence — Trade Record

| Attribute | Detail |
|-----------|--------|
| **File** | `database.py:97-130` |
| **Class** | `Trade` (SQLAlchemy model) |
| **Table** | `trades` |
| **Input** | INSERT from `TradeEngine.create_trade()` |
| **Output** | Persistent row in `trades` table |
| **Dependencies** | PostgreSQL via SQLAlchemy |
| **Implementation status** | **Complete** |

**Written columns:** `signal_id`, `symbol`, `side`, `entry`, `stop`, `tp1`, `tp2`, `rr`, `status="OPEN"`, `created_at`

**Unwritten columns:** `exit_price` (NULL), `closed_at` (NULL), `close_reason` (NULL), `exchange_order_id` (NULL), `pnl` (default 0)

**`tp2` is always written** but **never read** by any close or monitoring logic in the entire codebase.
**`exchange_order_id` is never written** anywhere in the codebase.

---

### Phase 6: Monitoring — `PaperExecutor.monitor_open_trades()`

Called from `ExecutionLoop.run_once()` line 56. Even when Phase 3 creates 0 new trades, this runs against any pre-existing open trades.

| Attribute | Detail |
|-----------|--------|
| **File** | `execution/paper_executor.py:171-185` |
| **Class** | `PaperExecutor` |
| **Function** | `monitor_open_trades()` |
| **Input** | None (reads from DB) |
| **Output** | `list[TradeMonitorResult]` |
| **Side effects** | DB updates: PnL for open trades, status/exit/close metadata for closed trades |
| **Dependencies** | `Trade` model, `get_session()`, `HyperliquidCollector` |
| **Error handling** | Catches all exceptions, rolls back, logs, returns `[]` |
| **Implementation status** | **Complete** |

**6a. Delegation chain:**

| # | Function | Lines | Input | Output |
|---|----------|-------|-------|--------|
| 6a | `monitor_open_trades()` | 171-185 | None | `list[TradeMonitorResult]` |
| 6b | `_monitor_trades(session, trades)` | 263-270 | Session + Trade list | `list[TradeMonitorResult]` |
| 6c | `_monitor_trade(session, trade)` | 272-305 | Session + single Trade | `TradeMonitorResult` |

**6c. `_monitor_trade()` detailed sequence:**

| # | Action | Line(s) | Details |
|---|--------|---------|---------|
| 1 | `get_current_price(symbol)` | 254-261 | Strips `USDT`, calls `HyperliquidCollector.get_ohlcv(limit=2)`, returns `close.iloc[-1]` |
| 2 | `calculate_pnl(trade, current_price)` | 231-242 | `price_delta = current - entry`; negated for SHORT; computes percentage |
| 3 | `trade.pnl = pnl.unrealized_pnl` | 275 | In-memory ORM field update |
| 4 | `_close_status_for_price(trade, current_price)` | 324-344 | Checks `tp1` and `stop` only — `tp2` is ignored |
| 5a | If TP/SL hit: `_close_trade_record()` | 279-294 | Sets `status`, `exit_price`, `close_reason`, `closed_at`, `pnl` |
| 5b | If still open: `session.add(trade)` | 296 | Redundant (already in session) |
| 6 | Return `TradeMonitorResult` | 356-371 | Built from current state |

**`_close_status_for_price()` at lines 324-344:**

- LONG: `price >= tp1` → `"TP_HIT"`, `price <= stop` → `"SL_HIT"`
- SHORT: `price <= tp1` → `"TP_HIT"`, `price >= stop` → `"SL_HIT"`
- Returns `None` if no boundary crossed

**`_close_trade_record()` at lines 307-322:**

Sets `status`, `exit_price`, `close_reason`, `closed_at = datetime.now(timezone.utc)`, `pnl`. Accumulates in instance dicts `_realized_pnl` and `_pnl_percentages`.

**Critical finding at line 296:** `session.add(trade)` for still-open trades. The trade was already loaded by `session.query()` at line 176 — this is a no-op. However, `session.commit()` at line 178 persists `trade.pnl`, meaning **unrealized PnL is written to the database on every monitoring cycle**, overwriting any previous value.

**Critical finding at lines 81-82:** Instance dicts `_pnl_percentages` and `_realized_pnl` accumulate entries over the lifetime of `PaperExecutor`. For long-running processes, these grow **unbounded**.

---

### Phase 7: Trade Close

| Attribute | Detail |
|-----------|--------|
| **File** | `execution/paper_executor.py:307-322` |
| **Class** | `PaperExecutor` |
| **Function** | `_close_trade_record()` |
| **Input** | Trade ORM object, exit_price, status, close_reason, TradePnL |
| **Output** | None (mutates ORM object in-memory) |
| **Side effects** | DB UPDATE on commit: `status`, `exit_price`, `close_reason`, `closed_at`, `pnl` |
| **Dependencies** | `datetime`, `Trade` model |
| **Error handling** | None |
| **Implementation status** | **Complete** |

The final close writes: `status = "TP_HIT"` or `"SL_HIT"`, `exit_price` = current market price, `close_reason` = same as status, `closed_at` = UTC now, `trade.pnl` = unrealized PnL at close.

`calculate_realized_pnl()` at lines 244-252 is a wrapper around `calculate_pnl()` that sets `realized_pnl = unrealized_pnl`. For paper trading this is correct — there are no fees, slippage, or settlement differences.

**TP2 is never checked.** The `Trade.tp2` column is written at trade creation but never read by any function.

---

## Phase-by-Phase Status Summary

| Phase | File | Class / Function | Status | Blocks Flow? |
|-------|------|------------------|--------|--------------|
| 0 — Signal Generation | `signal_generator.py` | `create_signal()` | **Dead Code** | No |
| 1a — Entry point | `app.py:5-13` | `main()` | **Complete** | No |
| 1b — Engine init | `core/engine.py:13-17` | `DecisionEngine.__init__()` | **Complete** | No |
| 1c — Run loop | `core/engine.py:95-109` | `DecisionEngine.run()` | **Complete** | No |
| 2 — Signal evaluation | `core/engine.py:26-76` | `DecisionEngine.process_signal()` | **Complete** | No |
| 3 — Orchestration | `execution/execution_loop.py:44-62` | `ExecutionLoop.run_once()` | **Partial** | **YES** |
| 3b — Pipeline | `execution/pipeline.py:96-139` | `DecisionPipeline.evaluate()` | **Partial** | No |
| 4 — Trade creation | `execution/trade_engine.py:10-64` | `TradeEngine.create_trade()` | **Complete** | No |
| 4a — TP/SL calc | `execution/tp_sl.py:3-36` | `TPSLEngine.calculate()` | **Complete** | No |
| 5 — DB persistence | `database.py:97-130` | `Trade` model | **Complete** | No |
| 6 — Monitoring | `execution/paper_executor.py:171-185` | `PaperExecutor.monitor_open_trades()` | **Complete** | No |
| 7 — Trade close | `execution/paper_executor.py:307-322` | `PaperExecutor._close_trade_record()` | **Complete** | No |

---

## Findings Catalog

### Missing Connections (Execution Breaks)

| ID | Finding | Evidence | Status |
|----|---------|----------|--------|
| MC1 | `DecisionEngine` passes `TradeCandidate` where `TradingSignal` is required | `core/engine.py:54` → `execution/execution_loop.py:44`: `run_once()` type signature expects `Iterable[TradingSignal]` | **Resolved** — Protocol satisfied by adding `id` field |
| MC2 | `TradeCandidate` lacks `id` field required by `DecisionPipeline._validate_signal()` | `execution/pipeline.py:61-72`: `TradeCandidate` dataclass had no `id` field | **Resolved** — `id: int` added, populated at both construction sites |
| MC3 | `_validate_signal()` raises `ValueError`, caught by `except Exception`, returns `None` | `execution/pipeline.py:137-139`: error silently swallowed, `None` returned | **Resolved** — validation passes now that `id` is present |
| MC4 | No status update propagates from `ExecutionLoop` back to `DecisionEngine` | `core/engine.py:54`: return value of `run_once()` is discarded; DB status stuck at `"APPROVED"` or `"STRONG_APPROVE"` | **Resolved** — `ExecutionLoop.process_signal()` calls `update_signal_status()` with `"REJECTED"` or `"EXECUTED"` |
| MC5 | No integrated signal source feeds the pipeline | Root `signal_generator.py` writes raw Signals; `execution/signal_generator.py` and `execution/live_signal_engine.py` write Trades directly (bypassing pipeline entirely) |

### Missing Data Propagation

| ID | Finding | Evidence | Status |
|----|---------|----------|--------|
| DP1 | `confidence` hardcoded to `0.0` | `core/engine.py:90`: `confidence=0.0` regardless of scores | Open |
| DP2 | `DecisionPipeline` computes scores independently, ignoring Phase 2 scores | Market data fetched twice (pipeline `_fetch_market_data()` at line 101, ScoringEngine at line 111) | Open |
| DP3 | `DecisionEngine` status (`"APPROVED"`/`"STRONG_APPROVE"`) never read by `DecisionPipeline` | Pipeline runs its own `ConfidenceEngine` independently with no visibility of prior status | Open |
| DP4 | Component scores never written to `Signal` DB record | `Signal` model has `trend_score`, `volume_score`, `btc_score`, `risk_score`, `score`, `confidence` columns — none are ever populated | Open |

### Broken Execution Paths

| ID | Finding | Evidence | Status |
|----|---------|----------|--------|
| BP1 | **Primary execution path was completely broken** | `DecisionEngine` → `ExecutionLoop` → `DecisionPipeline` → `TradeEngine` failed at the interface: `TradeCandidate` lacked `id`, `_validate_signal()` raised `ValueError`, pipeline returned `None` | **Resolved** — `id: int` added to `TradeCandidate`, populated at both construction sites |
| BP2 | `ConfidenceEngine` always returns `STRONG_APPROVE` | `core/confidence_engine.py:19`: `confidence * 100` pushes 0-100 range to 0-10000, clamped to 100 | Open |
| BP3 | `IndicatorEngine` references non-standard pandas_ta column name | `market_data/indicators.py:25`: `latest["ATRr_14"]` (double 'r'); standard pandas_ta output is `"ATR_14"`; triggers `KeyError`, caught by `ScoringEngine` fallback, returns all-zero scores, signal rejected at `< 0.55` threshold | Open |

### Placeholder Implementations

| ID | Finding | Evidence |
|----|---------|----------|
| PL1 | `BTCHealthFilter.evaluate()` returns hardcoded `{"ok": True}` | `filters/btc_filter.py:8-13`: ignores `data` parameter completely |
| PL2 | `filters/market_shock.py` is empty | 0 lines |
| PL3 | `config.MIN_SCORE = 85` defined but never referenced | `config.py:19` |
| PL4 | `config.MAX_OPEN_TRADES = 3` defined but never referenced | `config.py:20` |
| PL5 | `config.TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` loaded from env, never used | `config.py:12-13` |
| PL6 | `config.HL_API_KEY`, `HL_SECRET` loaded from env, never used | `config.py:15-16` |

### Dead Code

| ID | Finding | Evidence |
|----|---------|----------|
| DC1 | `execution/signal_generator.py` | Creates Trade with hardcoded `signal_id=999`, never imported by any module |
| DC2 | `execution/trade_seed.py` | Seeds one hardcoded BTC trade, never imported |
| DC3 | `execution/live_signal_engine.py` | `LiveSignalEngine` class writes Trades directly from Hyperliquid, never imported |
| DC4 | `scoring/regime_engine.py` | `RegimeEngine` class with market regime detection, never imported |
| DC5 | `codex_engine.py` | `apply_patch()` utility, unrelated to trading |
| DC6 | Root `signal_generator.py` | Generates random Signals, standalone script only |
| DC7 | `models/__init__.py`, `utils/__init__.py` | Empty placeholder modules |
| DC8 | `Trade.tp2` column | `database.py:111`: always written by `TPSLEngine`, **never read** by `PaperExecutor._close_status_for_price()` |
| DC9 | `Trade.exchange_order_id` column | `database.py:125`: never written by any code |

### Duplicate Responsibilities

| ID | Finding | Evidence |
|----|---------|----------|
| DR1 | Two independent scoring paths for the same signal | Phase 2: `DecisionEngine.process_signal()` → `ScoringEngine.score()` → threshold; Phase 3b: `DecisionPipeline.evaluate()` → `ScoringEngine.score()` → `ConfidenceEngine.calculate()` → gate |
| DR2 | `update_signal_status()` defined twice | `database.py:143` and `database.py:173` — second definition (after `if __name__ == "__main__":`) overwrites the first at module load |
| DR3 | Multiple `HyperliquidCollector` instances per evaluation cycle | Minimally 5: `ScoringEngine` (1), `DecisionPipeline` (1), `PaperExecutor` (1), `BTCHealth` (inside ScoringEngine), `MTFEngine` (inside ScoringEngine) |
| DR4 | Duplicate OHLCV fetches per evaluation | `DecisionPipeline._fetch_market_data()` (line 101, for no-op filter) + `ScoringEngine.score()` (line 26-29, for scoring) + `BTCHealth.score()` (line 33, internal) + `MTFEngine.score()` (line 35, 3 calls) = minimum 6 API calls per signal evaluation |

### Architecture Inconsistencies

| ID | Finding | Evidence |
|----|---------|----------|
| AI1 | Status string mismatch between old and new code paths | `"APPROVED"` (DecisionEngine, with D) vs `"APPROVE"` (ConfidenceEngine, without D); `APPROVED_DECISIONS` at `pipeline.py:21` checks `{"APPROVE", "STRONG_APPROVE"}` |
| AI2 | Mixed Turkish/English output | `core/engine.py:102`: `"Bekleyen sinyal yok."` |
| AI3 | Mixed logging conventions | `print()` in `core/engine.py`, `execution/trade_engine.py`, `database.py`, `scoring/scoring_engine.py`; `logging` in `execution/execution_loop.py`, `execution/pipeline.py`, `execution/paper_executor.py` |
| AI4 | No status state machine | Signal and Trade status are raw `String(30)` columns with no enum, no validation, no transition rules |
| AI5 | Empty placeholder modules and directories | `models/`, `utils/`, `.agents/`, `.codex/` — all empty |

### Hidden Assumptions

| ID | Finding | Evidence |
|----|---------|----------|
| HA1 | `signal.symbol` always ends with `"USDT"` | `.replace("USDT", "")` used in 4 locations: `core/engine.py` (via ScoringEngine), `execution/pipeline.py:147`, `market_data/mtf.py:13`, `execution/paper_executor.py:416` |
| HA2 | DataFrame from API always has at least 1 row | `.iloc[-1]` used without length check in `market_data/indicators.py:18`, `scoring/scoring_engine.py:54` |
| HA3 | Hyperliquid API always responds within 20s | Hardcoded `timeout=20` at `market_data/collector.py:22` |
| HA4 | PostgreSQL always available | No connection retry, no fallback, no health check |
| HA5 | `atr` key always exists in scores dict | `scoring/scoring_engine.py:52`: direct `values["atr"]` access (unsafe); `execution/execution_loop.py:93`: `.get("atr")` (safe) |

### Potential Runtime Failures

| ID | Finding | Evidence |
|----|---------|----------|
| RF1 | DB unreachable crashes entire process | `DecisionEngine.run()` has no error handling; `app.py:7` `create_tables()` will raise unhandled exception |
| RF2 | `ATRr_14` typo causes `KeyError` in `IndicatorEngine` | `market_data/indicators.py:25`: `latest["ATRr_14"]` — if pandas_ta emits `"ATR_14"` (single r), this fails; caught by `ScoringEngine` fallback, returns all zeros, signal rejected |
| RF3 | Empty DataFrame causes `IndexError` | `.iloc[-1]` on empty DataFrame in `indicators.py:18` and `scoring_engine.py:54` |
| RF4 | Rate limiting on Hyperliquid API | No backoff, no retry, 5+ parallel collector instances per cycle |
| RF5 | Unbounded instance dicts | `PaperExecutor._pnl_percentages` and `_realized_pnl` at lines 81-82 grow over the lifetime of the process |

### Missing Validation

| ID | Finding | Evidence |
|----|---------|----------|
| MV1 | No environment variable validation at startup | `config.py` loads values without checking required fields |
| MV2 | No response validation from Hyperliquid | `collector.py:27` assumes `response.json()` is always a list of candles |
| MV3 | No DB schema validation | `create_tables()` calls `metadata.create_all()` without migration checks or versioning |
| MV4 | No unique constraint on `Trade.signal_id` | Duplicate detection is at application level (`trade_engine.py:24-30`) only, not DB level |
| MV5 | No entry price bounds validation | `TPSLEngine` accepts any float, including negative or zero |

### Missing Persistence

| ID | Finding | Evidence | Status |
|----|---------|----------|--------|
| MP1 | Component scores never saved to `Signal` record | `Signal` model has 11 score columns; `ScoringEngine.score()` computes all of them; `DecisionEngine` writes none | Open |
| MP2 | `DecisionPipeline` decision not persisted to DB | Pipeline returns `None` on rejection but never updates signal status in database | **Resolved** — `ExecutionLoop.process_signal()` calls `update_signal_status()` with `"REJECTED"` or `"EXECUTED"` |

### Missing Logging

| ID | Finding | Evidence |
|----|---------|----------|
| ML1 | `DecisionEngine.process_signal()` uses `print()` | Lines 29-32, 38, 42, 47, 52, 65, 75 |
| ML2 | `TradeEngine.create_trade()` uses `print()` | Lines 34, 59 |
| ML3 | `ScoringEngine.score()` uses `print()` for errors | Line 38 |
| ML4 | `database.py` uses `print()` for DB errors | Lines 158, 188 |
| ML5 | No structured logging | All logging is plain string formatting with no correlation IDs |
| ML6 | No trade lifecycle audit log | Only the DB record exists; no event log for rejections, approvals, or close decisions |

### Missing Testing

| ID | Finding | Evidence |
|----|---------|----------|
| MT1 | Zero test assertions | All 8 `test_*.py` files print results to stdout without a single assertion |
| MT2 | No test framework | No `pytest.ini`, no test runner configuration, no `pytest` in `requirements.txt` |
| MT3 | No mocking | Tests call the real Hyperliquid API over the network |
| MT4 | No integration test | `test_pipeline.py` calls `DecisionPipeline.evaluate()` with a real API call |
| MT5 | No coverage for `ConfidenceEngine` math bug | The always-STRONG_APPROVE bug has zero test coverage |
| MT6 | No coverage for `TPSLEngine` invariant | R:R always 1.33 has zero test coverage |
| MT7 | No coverage for the interface break | `TradeCandidate` → `TradingSignal` incompatibility had zero test coverage | **Resolved** — interface mismatch fixed; no assertion test added |

---

## Scoring

| Category | Score | Rationale |
|----------|-------|-----------|
| **Architecture** | **4/10** | Clean dependency injection and Protocol-based interfaces exist in `execution/` (pipeline, execution_loop, paper_executor). The primary interface break (`TradeCandidate`/`TradingSignal`) is resolved. Signal status now persists through the pipeline. However, two competing architectures still coexist: the old `DecisionEngine`/`ConfidenceEngine` and the new `DecisionPipeline`/`ExecutionLoop` do the same work independently with no shared state. Duplicate API calls and duplicate scoring inflate latency and cost. |
| **Production Readiness** | **3/10** | The primary execution path (`app.py` → `DecisionEngine` → `ExecutionLoop` → `TradeEngine` → DB) can now create trades. Pipeline decisions are persisted to the Signal DB record. However, indicator data is all zeros (`ATRr_14` typo) and confidence is always 100 (math bug). No startup validation, no structured error handling, no retry logic, no rate limiting, no connection pooling strategy. Unbounded memory growth in `PaperExecutor`. Eight configuration values loaded from env are never used. |
| **Reliability** | **3/10** | The `PaperExecutor` monitoring and close logic is the most reliable component — it works correctly for pre-existing trades loaded from the database. The execution path now completes end-to-end. Remaining issues: ConfidenceEngine math bug, `ATRr_14` typo, BTCHealthFilter stub. Zero test assertions, zero mocking, zero test framework. |

---

## Priorities (Ordered by Impact)

| Rank | Priority | Category | Impact | Status |
|------|----------|----------|--------|--------|
| **1** | Fix the `DecisionEngine` → `ExecutionLoop` interface type mismatch | Missing Connection | **Primary execution path was completely broken.** `TradeCandidate` lacked `id`. `_validate_signal()` raised `ValueError`. Pipeline returned `None`. No trade was ever created. | **Done** — `id: int` added to `TradeCandidate` |
| **2** | Fix the `ConfidenceEngine` math bug | Broken Path | Component scores are 0–1. Weighted sum produces 0–100. `* 100` pushes to 0–10000. Clamped to 100, every non-trivial input triggers `STRONG_APPROVE`. | Open |
| **3** | Fix the `ATRr_14` column name in `IndicatorEngine` | Potential Runtime Failure | `market_data/indicators.py:25` references `"ATRr_14"` (double 'r'). Standard pandas_ta output is `"ATR_14"`. | Open |
| **4** | Eliminate duplicate market data fetching | Duplicate Responsibility | Minimum 6 API calls per evaluation when 1 suffices. | Open |
| **5** | Reconcile dual scoring paths into one | Architecture | Phase 2 and Phase 3b score independently with potentially different results. | Open |
| **6** | Remove dead code | Maintainability | 7 unreferenced files, 9 dead artifacts. | Open |
| **7** | Implement signal status persistence from `DecisionPipeline` | Missing Persistence | Pipeline decision was never recorded in Signal DB record. | **Done** — `ExecutionLoop` sets `"REJECTED"` or `"EXECUTED"` |
| **8** | Add startup validation and structured error handling | Reliability | No env validation, no DB connectivity check, no recovery. | Open |
| **9** | Normalize logging across all modules | Inconsistency | `print()` vs `logging`, Turkish/English mixed. | Open |
| **10** | Add assertion-based tests with fixtures and mocking | Testing | 8 scripts, zero assertions, no test framework. | Open |

---

## Infrastructure Review

### Dockerfile

| Attribute | Detail |
|-----------|--------|
| **File** | `Dockerfile` |
| **Base image** | `python:3.12-slim` |
| **Build type** | Single-stage |
| **COPY** | `. .` — copies entire context, including `.env`, `venv/`, `.git/`, `__pycache__/`, `*.pyc` |
| **Install** | `pip install --no-cache-dir -r requirements.txt` — no hash pinning, no version constraints |
| **User** | `root` (default) — no `USER` directive |
| **Healthcheck** | None |
| **CMD** | `python app.py` — hardcoded, no entrypoint wrapper |
| **.dockerignore** | None — `.git`, `venv/`, `__pycache__/`, `.env` all copied into the image |

**Finding DF1** — No `.dockerignore` exists. The Docker build context includes virtual environments, `.git` history, and any `.env` file containing secrets. The `.env` is listed in `.gitignore` but is not excluded from Docker builds.

**Finding DF2** — Container runs as root. No `USER` directive. Arbitrary code execution in the container has full system access.

**Finding DF3** — No health check. A container running with a hung Python process would appear "healthy" to orchestration systems.

**Finding DF4** — No version pinning. The `requirements.txt` contains no version constraints. Builds are non-reproducible — `pip install` on different dates produces different dependency versions.

### Dependencies (`requirements.txt`)

| Package | Declared | Actually Used | Notes |
|---------|----------|---------------|-------|
| `fastapi` | Yes | No | Not imported anywhere |
| `uvicorn` | Yes | No | Not imported anywhere |
| `sqlalchemy` | Yes | Yes | Core dependency |
| `psycopg2-binary` | Yes | Yes | PostgreSQL driver |
| `requests` | Yes | Yes | Hyperliquid API calls |
| `python-dotenv` | Yes | Yes | Env loading |
| `pandas` | Yes | Yes | DataFrame operations |
| `numpy` | Yes | No | Not imported anywhere |
| `tenacity` | Yes | No | Retry library, not used anywhere |
| `websocket-client` | Yes | No | Not imported anywhere |
| `colorlog` | Yes | No | Colored logging, not used anywhere |
| `pandas_ta` | **No** | **Yes** | **MISSING** — imported in `market_data/indicators.py:1` |

**Finding DP1** — `pandas_ta` is imported by `market_data/indicators.py` but is **absent from `requirements.txt`**. Running `pip install -r requirements.txt` produces an environment where `IndicatorEngine` raises `ModuleNotFoundError`. This is a critical runtime blocker.

**Finding DP2** — 6 of 11 declared packages are **unused**: `fastapi`, `uvicorn`, `numpy`, `tenacity`, `websocket-client`, `colorlog`. These inflate image size, increase the attack surface, and mislead developers.

**Finding DP3** — No version constraints on any dependency. `requirements.txt` is a flat list of package names with zero pinning.

### Documentation

**Finding DC1** — `README.md` contains 3 lines:

```
Elite Decision Engine

Version 1
```

There is no setup guide, environment configuration, architecture overview, usage instructions, or test commands. The only documentation about the system's intended behavior is `CLAUDE.md`.

**Finding DC2** — `.env.example` defines 7 configuration keys but does not indicate which are required, which have defaults, or what valid values are. `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD` have empty values with no guidance.

---

## Database Layer Analysis (Expanded)

### Foreign Key Integrity

**Finding DB1** — `Trade.signal_id` is defined as `Column(Integer)` at `database.py:102` with **no `ForeignKey` constraint**. If a `Signal` row is deleted, its associated `Trade` rows become orphaned. Referential integrity is not enforced at the database level.

### Dual Env Loading

**Finding DB2** — Both `config.py:9` and `database.py:21` call `load_dotenv()` independently. Both use default arguments (search for `.env` in CWD). This is redundant but harmless because `python-dotenv` only sets env vars that are not already set.

### Dual Database URL Construction

**Finding DB3** — `config.py` defines `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` via `os.getenv()`. `database.py` defines `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` via `os.getenv()` with separate defaults. Both construct a `DATABASE_URL` string independently. `engine.py` imports `CHECK_INTERVAL` from `config.py` but never uses `config.py`'s database URL — it uses `database.py`'s engine. The two sources can diverge silently.

### `update_signal_status` Redefinition

**Finding DB4** — `update_signal_status()` is defined twice at `database.py:143` and `database.py:173`. The second definition appears **after the `if __name__ == "__main__"` block at line 169-171**, meaning it is at module scope and executes at import time. Python's module loading overwrites the first definition with the second for any module importing `update_signal_status` from `database.py`. The second definition calls `SessionLocal()` directly instead of `get_session()`, but otherwise behaves identically.

### `Signal` Model — Unused Columns

**Finding DB5** — The `Signal` SQLAlchemy model at `database.py:57-91` defines 17 columns. Only 8 are ever written by application code: `id`, `symbol`, `side`, `timeframe`, `price`, `score` (partial), `status`, `created_at`. The following 9 columns are **never populated**:

| Column | Type | Defined at | Written by |
|--------|------|------------|------------|
| `divergence` | `String(50)` | line 65 | None |
| `confidence` | `Float` | line 70 | None |
| `market_health` | `Float` | line 72 | None |
| `btc_health` | `Float` | line 73 | None |
| `volume_score` | `Float` | line 75 | None |
| `funding_score` | `Float` | line 76 | None |
| `oi_score` | `Float` | line 77 | None |
| `cvd_score` | `Float` | line 78 | None |
| `trend_score` | `Float` | line 79 | None |
| `risk_score` | `Float` | line 80 | None |
| `approved` | `Boolean` | line 82 | None |
| `reason` | `Text` | line 87 | None |

`ScoringEngine.score()` computes `trend_score`, `volume_score`, `btc_score`, `mtf_score`, `risk_score`, and `final_score` — none of which are ever written back to the `Signal` record.

### `Trade` Model — Foreign Key Omission

**Finding DB6** — `Trade.signal_id` at `database.py:102` is `Column(Integer)` with no `ForeignKey("signals.id")`. No CASCADE DELETE behavior, no database-level referential integrity check.

---

## Testing Architecture — Full Analysis

All 8 test files are located at the repository root and follow an identical pattern: import component, call one function, print result. None use a testing framework, assertions, fixtures, or mocking.

| Test File | Tests | Calls Real API? | Has Assertions? | Framework |
|-----------|-------|-----------------|-----------------|-----------|
| `test_btc.py` | `BTCHealth.score()` | Yes (Hyperliquid) | No | None |
| `test_collector.py` | `HyperliquidCollector.get_ohlcv()` | Yes | No | None |
| `test_indicators.py` | `IndicatorEngine.calculate()` | Yes (via collector) | No | None |
| `test_mtf.py` | `MTFEngine.score()` | Yes (3 API calls) | No | None |
| `test_pipeline.py` | `DecisionPipeline.evaluate()` | Yes (via components) | No | None |
| `test_score.py` | `ScoringEngine.score()` | Yes (5+ API calls) | No | None |
| `test_volatility.py` | `VolatilityEngine.score()` | Yes (via collector) | No | None |
| `test_volume.py` | `VolumeEngine.score()` | Yes (via collector) | No | None |

**Finding TA1** — All 8 test files call the live Hyperliquid API. Test execution is network-dependent, rate-limited, and produces non-deterministic results. Tests fail if the API is down or rate-limited.

**Finding TA2** — Zero tests have assertions. `test_score.py` line 14 prints `result` but never checks it. `test_pipeline.py` line 29 prints `"APPROVED"` or `"REJECTED"` but never asserts. All tests pass 100% of the time regardless of correctness.

**Finding TA3** — No test runner configuration exists. No `pytest.ini`, `setup.cfg`, `pyproject.toml` test configuration, or `unittest` test loader. `pytest` is not listed in `requirements.txt`.

**Finding TA4** — Tests produce side effects. `test_score.py`, `test_pipeline.py`, and `test_mtf.py` trigger `HyperliquidCollector` API calls that count against rate limits. Running all 8 tests sequentially makes a minimum of 8+ API calls per run.

---

## Security Findings

| ID | Finding | Severity | Evidence |
|----|---------|----------|----------|
| SF1 | Container runs as root | High | `Dockerfile` has no `USER` instruction; default is root |
| SF2 | No `.dockerignore` | Medium | `.env`, `venv/`, `.git/` are copied into the image, potentially leaking secrets |
| SF3 | Default insecure DB credentials in code | High | `database.py:30-31`: `DB_USER = "postgres"`, `DB_PASSWORD = "postgres"` are hardcoded fallbacks |
| SF4 | DB password in connection string | Medium | `DATABASE_URL` at `database.py:33-36` embeds password in a URL string — exposed in process listings, error messages, logs |
| SF5 | Telegram token and chat ID loaded but never validated | Medium | `config.py:12-13`: loaded from env but never checked for presence or format |
| SF6 | HL API key and secret loaded but never validated | Medium | `config.py:15-16`: loaded from env but never used or validated |
| SF7 | No input sanitization on API responses | Low | `collector.py:27`: `response.json()` assumed to be a list of candles; unexpected formats propagate unhandled |

---

## Additional Technical Findings

| ID | Finding | Category | Evidence |
|----|---------|----------|----------|
| AF1 | `pandas_ta` missing from `requirements.txt` | Runtime Failure | `market_data/indicators.py:1` imports `pandas_ta`; `pip install -r requirements.txt` does not install it. `IndicatorEngine.calculate()` throws `ModuleNotFoundError` on first call |
| AF2 | `RiskEngine.score()` subtracts volatility score — inverted logic | Potential Bug | `scoring/risk_engine.py:12`: `risk_score -= volatility["score"] * 0.60`. Higher volatility reduces the risk score (making it appear "safer"), when logically it should increase perceived risk |
| AF3 | `RegimeEngine` ATR threshold not price-normalized | Hidden Assumption | `scoring/regime_engine.py:10`: `if atr < 150` compares ATR as a raw value; for BTC at $80K this is 0.19%, for a $10 altcoin it is 1,500% |
| AF4 | `BTCHealth` located in `market_data/` instead of `scoring/` | Inconsistency | `BTCHealth` is a scoring component (returns a health score), not a market data collector, but lives in `market_data/btc_health.py` |
| AF5 | `PaperExecutor.open_trade()` and `TradeEngine.create_trade()` coexist | Duplicate Responsibility | Two independent mechanisms for creating `Trade` records; `PaperExecutor.open_trade()` is never called by any pipeline code |
| AF6 | Empty `filters/__init__.py` and `scoring/__init__.py` | Dead Code | Placeholder package marker files with no imports, no re-exports, no `__all__` |

---

## Updated Scoring

| Category | Previous Score | Updated Score | Rationale |
|----------|---------------|---------------|-----------|
| **Infrastructure** | N/A | **2/10** | Dockerfile has no healthcheck, runs as root, has no `.dockerignore`, and no version pinning. 6 of 11 declared dependencies are unused. `pandas_ta` — a critical runtime dependency — is missing from `requirements.txt`. README is 3 lines. No CI/CD configuration exists. |
| **Security** | N/A | **3/10** | Container runs as root. Default credentials fallback to `postgres`/`postgres`. No `.dockerignore` risks leaking secrets. 4 secret env vars loaded but never validated. DB password embedded in a URL connection string. |

---

## Expanded Priorities (11–15)

The original Top 10 priorities remain valid. The following new priorities extend the list:

| Rank | Priority | Category | Impact |
|------|----------|----------|--------|
| **11** | Add `pandas_ta` to `requirements.txt` | Runtime Failure | `pandas_ta` is imported by `IndicatorEngine.calculate()` but absent from `requirements.txt`. A fresh `pip install` crashes at the first indicator calculation. Every scoring path uses `IndicatorEngine`, so this blocks all signal processing. |
| **12** | Add `.dockerignore` and non-root user to Dockerfile | Security / Operations | Docker image includes `.env`, `venv/`, `.git/`, `__pycache__/`. Container runs as root. An `ENTRYPOINT` wrapper and health check would improve operational safety. |
| **13** | Prune unused dependencies from `requirements.txt` | Maintainability | 6 of 11 declared packages (`fastapi`, `uvicorn`, `numpy`, `tenacity`, `websocket-client`, `colorlog`) are never imported. These increase image size and suggest abandoned feature plans. |
| **14** | Add `ForeignKey` constraint on `Trade.signal_id` | Data Integrity | `Trade.signal_id` is a plain `Integer` with no foreign key enforcement. Signal deletion would orphan trades. Database-level referential integrity should backstop the application-level duplicate check. |
| **15** | Write a meaningful `README.md` | Documentation | The current README is 3 lines. New developers, deployers, and reviewers have no entry point to understand the system. |

---

## Overall Assessment

The Elite Decision Engine has a well-intentioned architecture with clean Protocol-based abstractions in the `execution/` layer, proper dependency injection in `ExecutionLoop` and `DecisionPipeline`, and a logical separation of concerns between signal evaluation, trade creation, and position monitoring. The `PaperExecutor` monitoring and close logic is the most reliable component — it correctly loads open trades from the database, checks TP/SL levels, calculates PnL, and closes positions.

### Changes implemented

| Change | Files | Effect |
|--------|-------|--------|
| Added `id: int` to `TradeCandidate` | `execution/pipeline.py`, `core/engine.py` | Pipeline validation no longer raises `ValueError`. The `TradingSignal` Protocol is satisfied. `TradeCandidate` flows through the full `DecisionEngine` → `ExecutionLoop` → `DecisionPipeline` → `TradeEngine` path. |
| Signal status persistence | `execution/execution_loop.py` | Pipeline outcome is recorded in the Signal DB record: `"REJECTED"` on rejection, `"EXECUTED"` on trade creation. |

### Remaining blockers

Two bugs still prevent a correct end-to-end paper trading flow:

1. **`ATRr_14` column name typo** (`market_data/indicators.py:25`): pandas_ta outputs `"ATR_14"` (single 'r'). The double-'r' lookup raises `KeyError`. The `ScoringEngine` catch block returns all-zero scores. Without the ConfidenceEngine bug (below), every signal would be rejected — but the ConfidenceEngine bug masks this by clamping all confidence to 100.

2. **`ConfidenceEngine` math bug** (`core/confidence_engine.py:19`): `confidence * 100` pushes the 0-100 weighted sum to 0-10000, clamped back to 100. Every input produces `STRONG_APPROVE`. The decision gate is dead.

These two bugs interact destructively: the `ATRr_14` typo ensures all scores are zero, and the ConfidenceEngine bug ensures everything is approved anyway. Fixing one without the other produces a worse outcome (zero trades or garbage approvals).

The pipeline now runs end-to-end and trades are created in the database, but the confidence/decision and indicator data within those trades are incorrect. Fixing the ConfidenceEngine math and the `ATRr_14` column name would make the system produce correct trade decisions with real indicator data.

---

*Review generated from source code analysis. All conclusions derived exclusively from committed code in the repository.*
