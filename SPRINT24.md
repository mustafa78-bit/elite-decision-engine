# Sprint 24 — Startup Health Check

## Objective

Implement a Startup Health Check system that verifies every critical dependency before processing the first trading signal. If one critical dependency fails, the engine MUST NOT start.

## Architecture

```
HealthStatus enum (HEALTHY / WARNING / FAILED)
        ↑
   HealthReport dataclass
        ↑
   HealthCheck class
        │
        ├── _check_database()       → session query
        ├── _check_logging()        → log dir writable
        ├── _check_config()         → mandatory vars present
        ├── _check_kill_switch()    → initialized & RUNNING
        ├── _check_execution_router() → available & valid mode
        ├── _check_paper_executor() → instantiate
        └── _check_live_executor()  → instantiate
               │
               ▼
          ExecutionLoop.run_once()
               │
               ├── HEALTHY  → process signals
               └── FAILED   → log CRITICAL, return empty result
```

## Health Checks

| # | Check | Method | Failure condition |
|---|-------|--------|-------------------|
| 1 | Database | `_check_database()` | Session creation or `SELECT 1` fails |
| 2 | Logging | `_check_logging()` | Log dir not writable or file create fails |
| 3 | Configuration | `_check_config()` | Any mandatory config var missing |
| 4 | Kill Switch | `_check_kill_switch()` | Not configured or not RUNNING |
| 5 | Execution Router | `_check_execution_router()` | Not configured or mode invalid |
| 6 | Paper Executor | `_check_paper_executor()` | `PaperExecutor()` raises |
| 7 | Live Executor | `_check_live_executor()` | `LiveExecutor()` raises |

**Mandatory config vars checked**: `DRY_RUN`, `MAX_OPEN_TRADES`, `ACCOUNT_EQUITY`, `CHECK_INTERVAL`, `MIN_SCORE`, `MAX_POSITION_SIZE_USD`, `RISK_PER_TRADE_PERCENT`, `ATR_MULTIPLIER`, `MIN_POSITION_QUANTITY`.

## Execution Flow

### Healthy startup

```
ExecutionLoop.run_once()
  └─ health_check is not None
       └─ health_check.run()
            ├─ database  → HEALTHY
            ├─ logging   → HEALTHY
            ├─ config    → HEALTHY
            ├─ kill_switch → HEALTHY
            ├─ router    → HEALTHY
            ├─ paper_executor → HEALTHY
            └─ live_executor → HEALTHY
         report.is_failed() == False
            └─ process signals normally
```

### Failed startup

```
ExecutionLoop.run_once()
  └─ health_check is not None
       └─ health_check.run()
            └─ any check → FAILED
         report.is_failed() == True
            ├─ log CRITICAL for each error
            └─ return ExecutionLoopResult(processed=0, created=0, trades=[], monitor_results=[])
```

### No health check configured (backward compatible)

```
ExecutionLoop.run_once()
  └─ health_check is None
       └─ process signals normally
```

## Modified Files

| File | Change |
|------|--------|
| `core/health_check.py` | **New** — `HealthStatus`, `HealthReport`, `HealthCheck` (154 lines) |
| `execution/execution_loop.py` | Import `HealthCheck`, `HealthStatus`; inject `health_check` param; guard `run_once()` |
| `tests/test_health_check.py` | **New** — 19 tests across 10 test classes (318 lines) |

## Tests (19 new, 190 → 209 total)

| Test class | Tests | What it covers |
|------------|-------|----------------|
| `TestHealthStatus` | 2 | Enum values and membership |
| `TestHealthReport` | 4 | `is_failed()` and default values |
| `TestHealthCheckHealthy` | 2 | All checks pass; warning on missing session factory |
| `TestHealthCheckDatabaseFailure` | 1 | `SELECT 1` raises |
| `TestHealthCheckLoggingFailure` | 1 | Log dir not writable |
| `TestHealthCheckConfigFailure` | 1 | Missing mandatory config var |
| `TestHealthCheckKillSwitchFailure` | 2 | Not running; not configured |
| `TestHealthCheckExecutionRouterFailure` | 1 | Not configured |
| `TestHealthCheckPaperExecutorFailure` | 1 | `PaperExecutor()` raises |
| `TestHealthCheckLiveExecutorFailure` | 1 | `LiveExecutor()` raises |
| `TestHealthCheckIntegrationExecutionLoop` | 3 | Aborts on FAILED, starts on HEALTHY, no-op when None |

## Git Diff

```diff
diff --git a/execution/execution_loop.py b/execution/execution_loop.py
index 0192252..06d815a 100644
--- a/execution/execution_loop.py
+++ b/execution/execution_loop.py
@@ -14,6 +14,7 @@ from dataclasses import dataclass
 from typing import Any, Iterable, Optional
 
 from config import DRY_RUN
+from core.health_check import HealthCheck, HealthStatus
 from core.kill_switch import KillSwitch
 from database import update_signal_status
 from execution.paper_executor import PaperExecutor, TradeMonitorResult
@@ -56,6 +57,7 @@ class ExecutionLoop:
         execution_router: Optional[ExecutionRouter] = None,
         dry_run: Optional[bool] = None,
         kill_switch: Optional[KillSwitch] = None,
+        health_check: Optional[HealthCheck] = None,
         logger: Optional[logging.Logger] = None,
     ) -> None:
         self.pipeline = pipeline or DecisionPipeline()
@@ -66,11 +68,27 @@ class ExecutionLoop:
         self.execution_router = execution_router
         self.dry_run = DRY_RUN if dry_run is None else dry_run
         self.kill_switch = kill_switch or KillSwitch()
+        self.health_check = health_check
         self.logger = logger or logging.getLogger(__name__)
 
     def run_once(self, signals: Iterable[TradingSignal]) -> ExecutionLoopResult:
         """Process a batch of signals and monitor open trades once."""
 
+        if self.health_check is not None:
+            report = self.health_check.run()
+            if report.is_failed():
+                self.logger.critical("Health check FAILED — aborting run_once")
+                for err in report.errors:
+                    self.logger.critical("  %s", err)
+                return ExecutionLoopResult(
+                    processed=0, created=0, trades=[], monitor_results=[],
+                )
+            self.logger.info(
+                "Health check passed: overall=%s duration=%sms",
+                report.overall_status.value,
+                report.duration_ms,
+            )
+
         processed = 0
         trades: list[Any] = []
```

## Remaining Blockers

None.

## Next Recommendation

**Sprint 25 — Wire `HL_WALLET_ADDRESS` from environment variable**: Add a `HL_WALLET_ADDRESS` config that `LiveExecutor` reads as the default `address` field when placing live orders. This is the last hardcoded value before the live path can produce a fully-realistic signed payload.
