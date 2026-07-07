# Sprint 23 — Emergency Kill Switch

## Objective

Add an emergency kill switch that instantly halts all trading (live and paper) at every entry point without restarting the process. The kill switch must be injectable, testable, and checked before any decision pipeline work or exchange adapter call.

## Architecture

```
EngineState enum (RUNNING / PAUSED / STOPPING / STOPPED)
        ↑
   KillSwitch class
        ↓
  ┌─────┼─────┐
  │     │     │
  ▼     ▼     ▼
Loop Live  Paper
```

**`EngineState`** — str enum with 4 states:
- `RUNNING` — normal operation
- `PAUSED` — soft stop (new signals rejected, existing trades continue)
- `STOPPING` — transitional state (logged as CRITICAL during panic)
- `STOPPED` — hard stop (all entry points blocked)

**`KillSwitch`** — state holder with 6 public methods:
- `enable()` → RUNNING
- `disable()` → STOPPED
- `pause()` → PAUSED
- `resume()` → RUNNING
- `panic_shutdown()` → STOPPING → STOPPED
- `is_running()` → bool
- `state()` → EngineState

## Execution Flow

### KillSwitch checked at 3 gates

1. **ExecutionLoop.process_signal()** — before `pipeline.evaluate(signal)`:
   ```
   if not kill_switch.is_running():
       log WARNING → return None
   ```

2. **LiveExecutor.execute()** — before `_order_builder.build()`:
   ```
   if not kill_switch.is_running():
       log WARNING → return LiveOrderResult(accepted=False, error=f"engine is {state}")
   ```

3. **PaperExecutor.open_trade_from_request()** — before `_validate_trade_request()`:
   ```
   if not kill_switch.is_running():
       log WARNING → return None
   ```

### panic_shutdown() sequence

1. Log `CRITICAL` — "PANIC SHUTDOWN initiated — state=STOPPING"
2. Set state → `STOPPING`
3. Set state → `STOPPED`
4. Log `CRITICAL` — "engine STOPPED — no new trades accepted"

## Modified Files

| File | Change |
|------|--------|
| `core/kill_switch.py` | **New** — `KillSwitch` class + `EngineState` enum (49 lines) |
| `execution/execution_loop.py` | Import + inject `KillSwitch`; check at `process_signal()` entry |
| `execution/live_executor.py` | Import + inject `KillSwitch`; check at `execute()` entry |
| `execution/paper_executor.py` | Import + inject `KillSwitch`; check at `open_trade_from_request()` entry |
| `tests/test_kill_switch.py` | **New** — 24 tests across 5 test classes (286 lines) |

## Tests (24 new, 166 → 190 total)

| Test class | Tests | What it covers |
|------------|-------|----------------|
| `TestEngineState` | 2 | Enum values, membership |
| `TestKillSwitch` | 8 | enable, disable, pause, resume, panic_shutdown, custom initial state |
| `TestKillSwitchIntegrationLiveExecutor` | 5 | execute blocked in STOPPED/PAUSED/STOPPING, allowed in RUNNING, no exchange call when blocked |
| `TestKillSwitchIntegrationPaperExecutor` | 4 | open_trade_from_request blocked in STOPPED/STOPPING, allowed in RUNNING, via open_trade |
| `TestKillSwitchIntegrationExecutionLoop` | 5 | signal skipped in STOPPED/PAUSED, allowed in RUNNING, panic before loop, router.execute blocked |

## Git Diff

```diff
diff --git a/execution/execution_loop.py b/execution/execution_loop.py
index 5e86608..0192252 100644
--- a/execution/execution_loop.py
+++ b/execution/execution_loop.py
@@ -14,6 +14,7 @@ from dataclasses import dataclass
 from typing import Any, Iterable, Optional
 
 from config import DRY_RUN
+from core.kill_switch import KillSwitch
 from database import update_signal_status
 from execution.paper_executor import PaperExecutor, TradeMonitorResult
 from execution.pipeline import DecisionPipeline, TradeCandidate, TradingSignal
@@ -54,6 +55,7 @@ class ExecutionLoop:
         position_sizer: Optional[PositionSizingEngine] = None,
         execution_router: Optional[ExecutionRouter] = None,
         dry_run: Optional[bool] = None,
+        kill_switch: Optional[KillSwitch] = None,
         logger: Optional[logging.Logger] = None,
     ) -> None:
         self.pipeline = pipeline or DecisionPipeline()
@@ -63,6 +65,7 @@ class ExecutionLoop:
         self.position_sizer = position_sizer or PositionSizingEngine()
         self.execution_router = execution_router
         self.dry_run = DRY_RUN if dry_run is None else dry_run
+        self.kill_switch = kill_switch or KillSwitch()
         self.logger = logger or logging.getLogger(__name__)
 
     def run_once(self, signals: Iterable[TradingSignal]) -> ExecutionLoopResult:
@@ -88,6 +91,15 @@ class ExecutionLoop:
     def process_signal(self, signal: TradingSignal) -> Optional[Any]:
         """Evaluate one signal and create a trade only when approved."""
 
+        if not self.kill_switch.is_running():
+            self.logger.warning(
+                "KillSwitch active (%s): signal skipped %s %s",
+                self.kill_switch.state().value,
+                getattr(signal, "symbol", "?"),
+                getattr(signal, "side", "?"),
+            )
+            return None
+
         candidate = self.pipeline.evaluate(signal)
         if candidate is None:
             self.logger.info(
diff --git a/execution/live_executor.py b/execution/live_executor.py
index e807ded..42cca09 100644
--- a/execution/live_executor.py
+++ b/execution/live_executor.py
@@ -16,6 +16,7 @@ from dataclasses import dataclass, field
 from datetime import datetime, timezone
 from typing import Any, Callable, Optional, Protocol
 
+from core.kill_switch import KillSwitch
 from database import Trade
 from execution.hyperliquid_adapter import HyperliquidReadOnlyAdapter, Position
 from execution.live_order import LiveOrderStatus
@@ -121,6 +122,7 @@ class LiveExecutor:
         order_builder: Optional[OrderBuilder] = None,
         payload_validator: Optional[PayloadValidator] = None,
         signature_engine: Optional[SignatureEngine] = None,
+        kill_switch: Optional[KillSwitch] = None,
         logger: Optional[logging.Logger] = None,
     ) -> None:
         self.exchange_adapter = exchange_adapter or SimulatedExchangeAdapter()
@@ -131,10 +133,21 @@ class LiveExecutor:
         self._order_builder = order_builder or OrderBuilder()
         self._payload_validator = payload_validator or PayloadValidator()
         self._signature_engine = signature_engine or SignatureEngine()
+        self._kill_switch = kill_switch or KillSwitch()
         self.logger = logger or logging.getLogger(__name__)
 
     def execute(self, candidate: Any, size: Any) -> LiveOrderResult:
         """Validate, build payload, sign, send, parse, and persist a live order."""
+        if not self._kill_switch.is_running():
+            state = self._kill_switch.state().value
+            self.logger.warning(
+                "LIVE order rejected by KillSwitch (%s): %s %s",
+                state,
+                getattr(candidate, "symbol", "?"),
+                getattr(candidate, "side", "?"),
+            )
+            return LiveOrderResult(accepted=False, error=f"engine is {state}")
+
         self.logger.info(
             "LIVE order execution started for %s %s",
             getattr(candidate, "symbol", "?"),
diff --git a/execution/paper_executor.py b/execution/paper_executor.py
index 9fb9596..df31dc9 100644
--- a/execution/paper_executor.py
+++ b/execution/paper_executor.py
@@ -16,6 +16,7 @@ from typing import Any, Callable, Iterable, Optional
 
 sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
+from core.kill_switch import KillSwitch
 from database import Trade, get_session
 from market_data.collector import HyperliquidCollector
 
@@ -71,12 +72,14 @@ class PaperExecutor:
         self,
         collector: Optional[HyperliquidCollector] = None,
         session_factory: Callable[[], Any] = get_session,
+        kill_switch: Optional[KillSwitch] = None,
         logger: Optional[logging.Logger] = None,
     ) -> None:
         """Create a paper executor with injectable infrastructure."""
 
         self.collector = collector or HyperliquidCollector()
         self.session_factory = session_factory
+        self._kill_switch = kill_switch or KillSwitch()
         self.logger = logger or logging.getLogger(__name__)
         self._pnl_percentages: dict[int, float] = {}
         self._realized_pnl: dict[int, float] = {}
@@ -109,6 +112,15 @@ class PaperExecutor:
     def open_trade_from_request(self, request: PaperTradeRequest) -> Optional[Trade]:
         """Open a paper trade from a request object."""
 
+        if not self._kill_switch.is_running():
+            self.logger.warning(
+                "Paper trade rejected by KillSwitch (%s): %s %s",
+                self._kill_switch.state().value,
+                request.symbol,
+                request.side,
+            )
+            return None
+
         self._validate_trade_request(request)
         symbol = self._normalize_symbol(request.symbol)
         side = self._normalize_side(request.side)
```

## Remaining Blockers

None.

## Next Recommendation

**Sprint 24 — Wire `HL_WALLET_ADDRESS` from environment variable**: Add a `HL_WALLET_ADDRESS` config that `LiveExecutor` reads as the default `address` field when placing live orders. This is the last hardcoded value before the live path can produce a fully-realistic signed payload.
