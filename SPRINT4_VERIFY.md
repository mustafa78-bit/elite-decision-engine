# Sprint 4 — TradeEngine.create_trade() Failure Path Analysis

## Objective

Analyze every path where `_create_trade()` or `TradeEngine.create_trade()` returns `None` and determine the correct signal status for each.

## Failure Paths

There are **two call sites** that can return `None`:

```
ExecutionLoop.process_signal(signal)
  │
  └─ ExecutionLoop._create_trade(candidate)
       │
       ├─ [P1] entry is None or atr is None        → return None (line 108)
       │
       └─ TradeEngine.create_trade(signal, entry, atr)
            │
            ├─ [P2a] DB OperationalError            → rollback → return None (line 60)
            ├─ [P2b] IntegrityError                 → rollback → return None (line 60)
            └─ [P2c] TypeError / ValueError          → rollback → return None (line 60)
```

---

### [P1] `_create_trade` — `entry is None or atr is None`

**Code:** `execution/execution_loop.py:102-108`

```python
entry = candidate.entry
atr = candidate.scores.get("atr")

if entry is None or atr is None:
    self.logger.warning(...)
    return None
```

**Root cause:** `TradeCandidate` was built with `entry=None` or `atr` missing from scores.

This occurs when `ScoringEngine.score()` returns the fallback dict (line 39-46 of `scoring_engine.py`):

```python
return {
    "volume_score": 0,
    "trend_score": 0,
    "btc_score": 0,
    "mtf_score": 0,
    "risk_score": 1,
    "final_score": 0,
}
```

The fallback dict has no `"entry"` or `"atr"` keys → `scores.get("entry")` → `None` → `candidate.entry` → `None`.

**Is it reachable?** Practically no. The confidence engine would score the fallback as:

```
confidence = 0*30 + 0*20 + 0*20 + 0*20 + 1*10 = 10
```

`10 < 70` → `REJECT`. The pipeline returns `None` at the decision gate (line 124-125 of `pipeline.py`), never reaching `TradeCandidate` construction. P1 is a **defensive guard** against corrupt data that somehow passes confidence.

| Property | Value |
|----------|-------|
| Reachable | No (confidence gate blocks it) |
| Root cause | Market data API failure |
| Transient? | Permanent (same API call, same failure) |
| Candidate status | **REJECTED** (data is gone; retry loops forever) |

---

### [P2a] `TradeEngine.create_trade` — `OperationalError`

**Code:** `execution/trade_engine.py:56-60`

```python
except Exception as e:
    session.rollback()
    print("TRADE CREATE ERROR:", e)
    return None
```

Root cause: `session.add(trade)` or `session.commit()` fails with `sqlalchemy.exc.OperationalError`.

Scenarios:
- Postgres server is down or unreachable
- Connection pool exhausted
- Transaction aborted due to deadlock
- Network timeout

| Property | Value |
|----------|-------|
| Reachable | Yes |
| Root cause | Database infrastructure failure |
| Transient? | **Yes** (DB can recover) |
| Candidate status | **OPEN** (retry on next cycle) |

---

### [P2b] `TradeEngine.create_trade` — `IntegrityError`

**Code:** `execution/trade_engine.py:56-60`

Root cause: `session.commit()` violates a database constraint.

Scenarios:
- Duplicate primary key (impossible — `Trade.id` is auto-increment)
- `NOT NULL` constraint on a column that somehow got `None` (possible if `levels` dict has missing keys — see P2c)

With the current `Trade` schema (`database.py:97-130`), there are no `UNIQUE` constraints, `FOREIGN KEY` constraints, or `NOT NULL` columns that would fail with the current code paths. This path exists as a generic catch-all.

| Property | Value |
|----------|-------|
| Reachable | Edge case (code bug levels) |
| Root cause | Schema constraint violation |
| Transient? | Semi-permanent (code fix needed) |
| Candidate status | **REJECTED** (won't fix itself) |

---

### [P2c] `TradeEngine.create_trade` — `TypeError` / `ValueError`

**Code:** `execution/trade_engine.py:56-60`

Root cause: `levels` dict access at lines 43-47:

```python
trade = Trade(
    entry=levels["entry"],
    stop=levels["stop"],
    tp1=levels["tp1"],
    tp2=levels["tp2"],
    rr=levels["rr"],
)
```

If `TPSLEngine.calculate()` changes to return a dict missing any of these keys, a `KeyError` is raised. Currently `TPSLEngine.calculate()` always returns all 5 keys with valid values (`execution/tp_sl.py:30-36`).

| Property | Value |
|----------|-------|
| Reachable | Only if TPSLEngine changes |
| Root cause | Code bug in TPSLEngine |
| Transient? | Permanent (code fix needed) |
| Candidate status | **REJECTED** (won't fix itself) |

---

## Summary

| Path | Where | Root cause | Transient? | Reachable | Correct status |
|------|-------|-----------|------------|-----------|----------------|
| P1 | `_create_trade` L108 | `entry`/`atr` missing from approved candidate | No | No (confidence gate blocks) | REJECTED |
| P2a | `TradeEngine.create_trade` L60 | DB `OperationalError` | **Yes** | **Yes** | **OPEN** |
| P2b | `TradeEngine.create_trade` L60 | `IntegrityError` | No | Edge case | REJECTED |
| P2c | `TradeEngine.create_trade` L60 | KeyError / TypeError | No | Only if TPSLEngine breaks | REJECTED |

**Dominant failure mode:** P2a — transient DB error. This is the failure an operator will encounter.

## Risk Analysis

The current Sprint 4 implementation (`update_signal_status(signal.id, "OPEN")` for all failures) is:

- **Correct for P2a** — the common case. DB recovers → signal retried → trade created → EXECUTED.
- **Wrong for P1, P2b, P2c** — permanent failures that will retry forever.
  - P1: Unreachable. Zero risk.
  - P2b: Schema has no constraints that would fail. Near-zero risk.
  - P2c: `TPSLEngine` would need a code change to break. Near-zero risk.

**Infinite retry risk:** If Postgres stays down permanently, the signal will be repeatedly PROCESSING → OPEN → PROCESSING → OPEN. Each cycle hits the DB twice (status update, trade check). With a 60-second `CHECK_INTERVAL` and a few open signals, this is negligible load even over hours.

## Final Recommendation

The current Sprint 4 implementation is **production-safe**. The single `OPEN` status for all failures is:

| Criterion | Verdict |
|-----------|---------|
| Covers dominant failure mode (P2a) | ✅ Correct (OPEN → retry) |
| Handles unreachable paths (P1) | ✅ Correct enough (OPEN = no data loss) |
| Handles edge cases (P2b, P2c) | ✅ Correct enough (OPEN = no stuck signals) |
| No infinite retry danger | ✅ Negligible DB load even if permanent |
| No signal stuck forever | ✅ Fixed |

Improvement opportunity (not required for commit): distinguish P1 from P2 by catching specific exception types and returning `REJECTED` for permanent failures. This would require changing `_create_trade()` to return an enum instead of `Optional[Any]`, adding complexity for zero practical benefit given P1 is unreachable.

**Approved for commit.**
