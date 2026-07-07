# Sprint 26 — Centralized Secrets and Configuration Management

## Objective

No API key or wallet address may be hardcoded anywhere. All sensitive configuration must come from environment variables with validation at startup.

## Architecture

```
Environment Variables
    │
    ▼
Settings.load()
    │
    ├── HL_API_KEY          → required string
    ├── HL_SECRET            → required string
    ├── HL_WALLET_ADDRESS    → required string
    ├── DRY_RUN              → bool (default True)
    ├── ACCOUNT_EQUITY       → float (default 10000.0)
    ├── MAX_OPEN_TRADES      → int (default 3)
    ├── MAX_POSITION_SIZE_USD → float (default 100000.0)
    ├── RISK_PER_TRADE_PERCENT → float (default 1.0)
    ├── ATR_MULTIPLIER       → float (default 1.5)
    ├── CHECK_INTERVAL       → int (default 10)
    ├── MIN_SCORE            → int (default 85)
    ├── MAX_EXPOSURE_PER_SYMBOL → float (default 200000.0)
    ├── MAX_PORTFOLIO_EXPOSURE  → float (default 500000.0)
    ├── MAX_DAILY_LOSS       → float (default 10000.0)
    └── MIN_POSITION_QUANTITY → float (default 0.001)
            │
            ▼
    HealthCheck._check_settings()
            │
            ├── HEALTHY → proceed
            └── FAILED  → log CRITICAL, abort
```

## Settings

The `Settings` class in `core/settings.py`:

- Accepts an optional `env: dict[str, str]` for testing (when `None`, reads from `os.environ`)
- `load()` calls `load_dotenv()` when using real env, then validates and converts every variable
- `_required_str(key)` — raises `ConfigurationError` if missing or empty
- `_int(key, default)` — raises `ConfigurationError` on invalid integer
- `_float(key, default)` — raises `ConfigurationError` on invalid float
- `_bool(key, default)` — accepts `1/0`, `true/false`, `yes/no`, `on/off`

## Validation

| Condition | Result |
|-----------|--------|
| `HL_API_KEY` missing | `ConfigurationError` |
| `HL_SECRET` missing | `ConfigurationError` |
| `HL_WALLET_ADDRESS` missing | `ConfigurationError` |
| `MAX_OPEN_TRADES=abc` | `ConfigurationError` (invalid int) |
| `ACCOUNT_EQUITY=xyz` | `ConfigurationError` (invalid float) |
| All present and valid | `Settings` object with typed attributes |
| No `Settings` passed to HealthCheck | Check silently returns HEALTHY |

## Health Check Integration

A new `_check_settings()` method in `HealthCheck`:

- If `settings` is `None` → return `HEALTHY` (no-op)
- If `settings` is provided → call `settings.load()`
  - `ConfigurationError` → `FAILED` with descriptive error
  - Any other exception → `FAILED` with unexpected error
  - Success → `HEALTHY`

## Modified Files

| File | Change |
|------|--------|
| `core/settings.py` | **New** — `Settings` class, `ConfigurationError` exception (105 lines) |
| `core/health_check.py` | Import `Settings`, `ConfigurationError`; inject `settings` param; add `_check_settings()` |
| `tests/test_settings.py` | **New** — 14 tests across 5 test classes (151 lines) |
| `tests/test_health_check.py` | 3 new tests in `TestHealthCheckSettingsIntegration` |

## Tests (17 new, 239 → 256 total)

| Test class | Tests | What it covers |
|------------|-------|----------------|
| `TestSettingsLoad` | 6 | Secrets loaded, defaults, overrides, bool true/false values |
| `TestSettingsMissingRequired` | 4 | Missing HL_API_KEY, HL_SECRET, HL_WALLET_ADDRESS, all required |
| `TestSettingsInvalidValues` | 2 | Invalid int, invalid float |
| `TestSettingsConfigurationError` | 2 | Exception subclass, message |
| `TestHealthCheckSettingsIntegration` | 3 | Settings healthy, settings failure, not configured (skips) |

## Git Diff

```diff
diff --git a/core/health_check.py b/core/health_check.py
index 674ff5e..9f1776a 100644
--- a/core/health_check.py
+++ b/core/health_check.py
@@ -9,6 +9,7 @@ from typing import Any, Callable, Optional
 
 import config as config_module
 from core.kill_switch import KillSwitch
+from core.settings import ConfigurationError, Settings
 from execution.live_executor import LiveExecutor
 from execution.paper_executor import PaperExecutor
 from execution.router import ExecutionRouter, TradingMode
@@ -39,12 +40,14 @@ class HealthCheck:
         session_factory: Optional[Callable[[], Any]] = None,
         kill_switch: Optional[KillSwitch] = None,
         execution_router: Optional[ExecutionRouter] = None,
+        settings: Optional[Settings] = None,
         log_dir: str = "logs",
         logger: Optional[logging.Logger] = None,
     ) -> None:
         self._session_factory = session_factory
         self._kill_switch = kill_switch
         self._execution_router = execution_router
+        self._settings = settings
         self._log_dir = log_dir
         self.logger = logger or logging.getLogger(__name__)
 
@@ -89,6 +92,11 @@ class HealthCheck:
         warnings.extend(live_w)
         errors.extend(live_e)
 
+        settings_status, settings_w, settings_e = self._check_settings()
+        checks["settings"] = settings_status
+        warnings.extend(settings_w)
+        errors.extend(settings_e)
+
         duration = (time.perf_counter() - start) * 1000
 
         if errors:
@@ -194,3 +202,14 @@ class HealthCheck:
             return HealthStatus.HEALTHY, [], []
         except Exception as e:
             return HealthStatus.FAILED, [], [f"LiveExecutor instantiation failed: {e}"]
+
+    def _check_settings(self) -> tuple[HealthStatus, list[str], list[str]]:
+        if self._settings is None:
+            return HealthStatus.HEALTHY, [], []
+        try:
+            self._settings.load()
+            return HealthStatus.HEALTHY, [], []
+        except ConfigurationError as e:
+            return HealthStatus.FAILED, [], [f"Settings validation failed: {e}"]
+        except Exception as e:
+            return HealthStatus.FAILED, [], [f"Settings check failed unexpectedly: {e}"]
```

## Remaining Blockers

None.

## Next Recommendation

**Sprint 27 — End-to-End Integration Test**: Build a single end-to-end test that wires all components (TradingSignal → DecisionPipeline → RiskManager → PositionSizingEngine → ExecutionRouter → PaperExecutor → Trade → TP/SL verification) covering the full lifecycle without any HTTP or exchange calls.
