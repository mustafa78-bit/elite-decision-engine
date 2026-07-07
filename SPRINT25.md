# Sprint 25 — Resilient Exchange Communication

## Objective

All external exchange/API calls must automatically recover from transient failures using retry, exponential backoff, and a circuit breaker.

## Architecture

```
RetryPolicy                     CircuitBreaker
   │                                │
   │  execute(fn)                   │  call(fn)
   │    ├─ attempt 1                │    ├─ CLOSED → pass through
   │    ├─ attempt 2 (2×delay)      │    ├─ OPEN → raise CircuitBreakerOpenError
   │    ├─ attempt 3 (4×delay)      │    └─ HALF_OPEN → probe one request
   │    └─ attempt 4 (8×delay)      │
   │                                │
   └──────────┬─────────────────────┘
              │
              ▼
  HyperliquidReadOnlyAdapter._post()
              │
              │ calls circuit_breaker.call(
              │   lambda: retry.execute(adapter._do_http_post, payload)
              │ )
              ▼
         _do_http_post(payload)
              │
              ▼
      session.post(INFO_URL, ...)
```

## Retry Flow

```
Attempt 1  →  failure   → log WARNING → sleep(1s)
Attempt 2  →  failure   → log WARNING → sleep(2s)
Attempt 3  →  failure   → log WARNING → sleep(4s)
Attempt 4  →  success   → log INFO    → return result
```

- `max_attempts` — configurable (default 4)
- `base_delay` — starting delay (default 1.0s)
- `backoff_multiplier` — exponential factor (default 2.0)
- `max_delay` — ceiling on each delay (default 60.0s)
- `retry_exceptions` — tuple of exception types to retry on

## Circuit Breaker

### States

```
                         failures ≥ threshold
       ┌─────────────────── CLOSED ───────────────────┐
       │                         ↑                    │
       │                         │                    │
       │                   success in                  │
       │                  HALF_OPEN                    │
       │                         │                    │
       ▼                         │                    ▼
      OPEN ──→ timeout ──→ HALF_OPEN ──→ failure ──→ OPEN
       │                                             │
       └─────────────────────────────────────────────┘
```

### Rules

| Condition | Action |
|-----------|--------|
| Failures < threshold | Stay CLOSED, increment counter |
| Failures ≥ threshold | Transition to OPEN, log CRITICAL |
| Call while OPEN | Raise `CircuitBreakerOpenError` |
| Timeout elapsed in OPEN | Transition to HALF_OPEN |
| HALF_OPEN + success | Transition to CLOSED, reset counter |
| HALF_OPEN + failure | Transition to OPEN |

### Defaults

- `failure_threshold` — 5
- `recovery_timeout` — 30.0 seconds

## Modified Files

| File | Change |
|------|--------|
| `core/retry.py` | **New** — `RetryPolicy` class with exponential backoff (60 lines) |
| `core/circuit_breaker.py` | **New** — `CircuitBreaker` class, `CircuitState` enum, `CircuitBreakerOpenError` (93 lines) |
| `execution/hyperliquid_adapter.py` | Import + inject `RetryPolicy` + `CircuitBreaker`; `_post()` wraps calls; new `_do_http_post()` |
| `tests/test_retry.py` | **New** — 13 tests across 3 test classes |
| `tests/test_circuit_breaker.py` | **New** — 13 tests across 6 test classes |
| `tests/test_hyperliquid_adapter.py` | 4 new tests in `TestHyperliquidAdapterRetry` + `TestHyperliquidAdapterCircuitBreaker` |

## Tests (30 new, 209 → 239 total)

| Test class | Tests | What it covers |
|------------|-------|----------------|
| `TestRetryPolicyConstructor` | 5 | Default values, invalid params |
| `TestRetryPolicyExecute` | 8 | First-attempt success, retry success, exhaustion, non-retryable, backoff sequence, max delay cap, single attempt, args passthrough |
| `TestCircuitBreakerConstructor` | 3 | Defaults, invalid threshold, invalid timeout |
| `TestCircuitBreakerClosed` | 3 | Call succeeds, failure increments count, threshold opens circuit |
| `TestCircuitBreakerOpen` | 2 | Blocks requests, transitions to half-open after timeout |
| `TestCircuitBreakerHalfOpen` | 2 | Success closes circuit, failure reopens |
| `TestCircuitBreakerReset` | 1 | Reset clears state and failure count |
| `TestCircuitBreakerStateProperty` | 2 | Timeout check on read, stays open before timeout |
| `TestHyperliquidAdapterRetry` | 2 | Retry succeeds after temporary HTTP failures, retry exhausts |
| `TestHyperliquidAdapterCircuitBreaker` | 2 | Circuit blocks after repeated failures, allows successful calls |

## Git Diff

```diff
diff --git a/execution/hyperliquid_adapter.py b/execution/hyperliquid_adapter.py
index be9e141..e9e7b2a 100644
--- a/execution/hyperliquid_adapter.py
+++ b/execution/hyperliquid_adapter.py
@@ -12,6 +12,9 @@ from typing import Any, Optional
 
 import requests
 
+from core.circuit_breaker import CircuitBreaker
+from core.retry import RetryPolicy
+
 INFO_URL = "https://api.hyperliquid.xyz/info"
 
 
@@ -75,9 +78,18 @@ class HyperliquidReadOnlyAdapter:
     def __init__(
         self,
         session: Optional[requests.Session] = None,
+        retry_policy: Optional[RetryPolicy] = None,
+        circuit_breaker: Optional[CircuitBreaker] = None,
         logger: Optional[logging.Logger] = None,
     ) -> None:
         self.session = session or requests.Session()
+        self._retry = retry_policy or RetryPolicy(
+            retry_exceptions=(
+                requests.exceptions.ConnectionError,
+                requests.exceptions.Timeout,
+            ),
+        )
+        self._circuit_breaker = circuit_breaker or CircuitBreaker()
         self.logger = logger or logging.getLogger(__name__)
 
     def get_account_state(self, address: str) -> AccountState:
@@ -200,8 +212,14 @@ class HyperliquidReadOnlyAdapter:
         return dict(data)
 
     def _post(self, payload: dict) -> Any:
-        """Send a POST request to the Hyperliquid /info endpoint."""
+        """Send a POST request via circuit breaker + retry."""
         self.logger.debug("POST %s payload=%s", INFO_URL, payload)
+        return self._circuit_breaker.call(
+            lambda: self._retry.execute(self._do_http_post, payload),
+        )
+
+    def _do_http_post(self, payload: dict) -> Any:
+        """Raw HTTP POST — may raise ConnectionError, Timeout, HTTPError."""
         response = self.session.post(INFO_URL, json=payload, timeout=20)
         response.raise_for_status()
         return response.json()
```

## Remaining Blockers

None.

## Next Recommendation

**Sprint 26 — End-to-End Integration Test**: Build a single end-to-end test that wires all components (TradingSignal → DecisionPipeline → RiskManager → PositionSizingEngine → ExecutionRouter → PaperExecutor → Trade → TP/SL verification) in LIVE mode with DRY_RUN=True, covering the full lifecycle without any HTTP or exchange calls.
