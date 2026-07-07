# Sprint 27 — End-to-End Integration Test

## Objective

Build a full End-to-End Integration Test that validates the entire trading pipeline from signal ingestion to trade persistence without any real HTTP requests or exchange interaction.

## Architecture (pipeline tested)

```
TradingSignal
      │
      ▼
DecisionPipeline (mocked → approves/rejects)
      │
      ▼
RiskManager (real or mocked)
      │
      ▼
PositionSizingEngine (real)
      │
      ▼
ExecutionRouter (PAPER or LIVE)
      │
      ▼
PaperExecutor / LiveExecutor
      │
      ▼
Trade (Database — SQLite test DB)
      │
      ▼
PortfolioEngine (reads from test DB)
      │
      ▼
PerformanceEngine (reads from test DB)
```

## Execution Flow

### Scenario 1 — Full Pipeline Success

```
Signal(id=1, BTCUSDT, LONG)
  → Pipeline.approve() → Candidate(id=1, entry=50000, scores={atr:500})
  → RiskManager.can_open_trade() → (True, "")
  → PositionSizingEngine.calculate() → PositionSize(qty=0.13, notional=6666.67)
  → Router._paper_execute() → TP/SL calculated (entry=50000, sl=49250, tp=51000)
  → PaperExecutor.open_trade() → Trade persisted in DB (status=OPEN)
  → update_signal_status(id=1, "EXECUTED")
  → PortfolioEngine.stats() → total_trades=1, open_trades=1
  → PerformanceEngine.stats() → sharpe=0.0, sortino=0.0 (no closed trades)
```

### Scenario 2 — Risk Rejection

```
Signal(id=2, ETHUSDT, SHORT)
  → Pipeline.approve() → Candidate
  → RiskManager.can_open_trade() → (False, "risk rejected by test")
  → Trade NOT created
  → update_signal_status(id=2, "REJECTED")
```

### Scenario 3 — KillSwitch Active

```
KillSwitch(state=STOPPED)
  → ExecutionLoop.process_signal()
  → kill_switch.is_running() == False
  → log WARNING → return None
  → Signal NOT processed, no trade created
```

### Scenario 4 — HealthCheck Failure

```
HealthCheck.run() → HealthReport(overall=FAILED)
  → ExecutionLoop.run_once()
  → log CRITICAL → return ExecutionLoopResult(processed=0, created=0)
```

### Scenario 5 — LIVE + DRY_RUN

```
DRY_RUN=True, TradingMode=LIVE
  → ExecutionLoop._execute() → router.mode==LIVE && dry_run==True
  → _dry_run() → router.prepare_order() → build → validate → sign → STOP
  → execute() NEVER called
  → No trade created
```

## Assertions

| Scenario | Assertions |
|----------|------------|
| Full pipeline | `processed==1`, `created==1`, trade fields correct, status OPEN, pnl 0.0, Signal.status == EXECUTED, Portfolio stats reflect open trade, Performance stats at defaults |
| Duplicate signal | Second `run_once` with same `signal.id` creates 0 new trades |
| Risk rejection | `created==0`, Signal.status == REJECTED |
| KillSwitch stopped | `created==0`, Signal not in DB (never processed) |
| KillSwitch running | `created==1` |
| HealthCheck FAILED | `processed==0`, `created==0` |
| HealthCheck HEALTHY | `processed==1`, `created==1` |
| Dry-run LIVE | `prepare_order()` returns ready/validated/signed, `execute()` not called |
| No dry-run LIVE | `execute()` called once, trade created |

## Modified Files

| File | Change |
|------|--------|
| `tests/test_end_to_end.py` | **New** — 10 tests across 6 test classes (280 lines) |

## Tests (10 new, 256 → 266 total)

| Test class | Tests | What it covers |
|------------|-------|----------------|
| `TestFullPipelineSuccess` | 2 | Full signal → trade → portfolio → performance; duplicate signal |
| `TestRiskRejection` | 1 | Risk rejection → signal REJECTED, no trade |
| `TestKillSwitchBlocksExecution` | 2 | KillSwitch STOPPED skips signal, RUNNING allows |
| `TestHealthCheckFailure` | 2 | HealthCheck FAILED aborts, HEALTHY proceeds |
| `TestLiveDryRun` | 3 | prepare_order runs, execute not called in dry_run, execute called when not dry_run |

## Git Diff

```diff
diff --git a/tests/test_end_to_end.py b/tests/test_end_to_end.py
new file mode 100644
index 0000000..[new]
--- /dev/null
+++ b/tests/test_end_to_end.py
@@ -0,0 +1,280 @@
+"""End-to-end integration test for the full trading pipeline.
+
+Five scenarios covering the complete signal → trade lifecycle:
+
+  1. Full pipeline success
+  2. Risk rejection
+  3. KillSwitch active
+  4. HealthCheck failure
+  5. LIVE + DRY_RUN
+
+No HTTP, no exchange calls, no external dependencies.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from unittest.mock import MagicMock
+
+import pytest
+
+from core.circuit_breaker import CircuitBreaker
+from core.health_check import HealthCheck, HealthReport, HealthStatus
+from core.kill_switch import EngineState, KillSwitch
+from core.retry import RetryPolicy
+from core.settings import Settings
+from execution.execution_loop import ExecutionLoop
+from execution.live_executor import LiveExecutor
+from execution.paper_executor import PaperExecutor
+from execution.router import ExecutionRouter, TradingMode
+from performance_engine import PerformanceEngine
+from portfolio_engine import PortfolioEngine
+from position_sizing import PositionSizingEngine
+from risk_manager import RiskManager
+
+
+@dataclass(frozen=True)
+class _Signal:
+    id: int = 1
+    symbol: str = "BTCUSDT"
+    side: str = "LONG"
+    timeframe: str = "1h"
+
+
+@dataclass(frozen=True)
+class _Candidate:
+    ...
+
+
+class _ApprovingPipeline:
+    ...
+
+
+class _RejectingPipeline:
+    ...
+
+
+@pytest.fixture
+def pipeline_approves():
+    return _ApprovingPipeline()
+
+...
+
+
+class TestFullPipelineSuccess:
+    def test_signal_to_trade_persistence(self, db_session, ...):
+        ...
+    def test_duplicate_signal_no_new_trade(self, db_session, ...):
+        ...
+
+
+class TestRiskRejection:
+    def test_risk_rejected_trade_not_created(self, db_session, ...):
+        ...
+
+
+class TestKillSwitchBlocksExecution:
+    ...
+
+
+class TestHealthCheckFailure:
+    ...
+
+
+class TestLiveDryRun:
+    ...
```

## Remaining Blockers

None.

## Next Recommendation

**Sprint 28 — CLI Dashboard Command**: Add a `python -m engine live` CLI command that displays open positions, portfolio stats, and performance metrics in a formatted table. Uses existing `PortfolioEngine`, `PerformanceEngine`, and `PaperExecutor` under the hood.
