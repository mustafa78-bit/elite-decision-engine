# Sprint 2 — Dependency Injection Verification

## Question

Is `ExecutionLoop()` (default arguments) functionally identical to `ExecutionLoop(trade_engine=self.trade_engine)` where `self.trade_engine = TradeEngine()`?

## Evidence

### Before Sprint 2 — `core/engine.py:16-17`

```python
self.trade_engine = TradeEngine()                                    # fresh instance
self.execution_loop = ExecutionLoop(trade_engine=self.trade_engine)  # injects it
```

### After Sprint 2 — `core/engine.py:12`

```python
self.execution_loop = ExecutionLoop()  # no arguments
```

### How ExecutionLoop handles the default — `execution/execution_loop.py:41`

```python
self.trade_engine = trade_engine or TradeEngine()
```

If `trade_engine` is `None` (default), a new `TradeEngine()` is created. If a `TradeEngine` instance is provided, it is used directly.

### What TradeEngine does at construction — `execution/trade_engine.py:7-8`

```python
def __init__(self):
    self.tp_sl = TPSLEngine()
```

No shared state, no singleton, no external connections, no file handles, no network sockets. Just creates a `TPSLEngine` (which is also stateless — a single `calculate()` method at `execution/tp_sl.py:3`).

### Instance comparison

| Aspect | Old: `ExecutionLoop(trade_engine=instance)` | New: `ExecutionLoop()` |
|--------|--------------------------------------------|------------------------|
| `trade_engine` argument | `TradeEngine()` instance | `None` (default) |
| Resolution | `instance or TradeEngine()` → instance | `None or TradeEngine()` → new `TradeEngine()` |
| Is a `TradeEngine` created? | Yes (explicitly by DecisionEngine) | Yes (by ExecutionLoop default) |
| Same instance? | Same as DecisionEngine's `self.trade_engine` | Fresh instance |
| Does instance identity affect behavior? | **No** | **No** |

### Why instance identity does not matter

`TradeEngine` has **no mutable shared state**. Every `create_trade()` call:

1. Calls `self.tp_sl.calculate(...)` — pure function, no side effects
2. Opens a new DB session via `get_session()`
3. Queries for existing trades
4. Inserts or returns existing
5. Closes the session

The `TPSLEngine` at `execution/tp_sl.py:3-36` is also stateless — it computes TP/SL levels from inputs with no instance-level storage.

## Conclusion

`ExecutionLoop()` with default arguments is **functionally identical** to `ExecutionLoop(trade_engine=self.trade_engine)`. No dependency injection behavior was lost. The only difference is which `TradeEngine` instance is used, and since `TradeEngine` has no persistent state between calls, the instance identity is irrelevant to correctness.
