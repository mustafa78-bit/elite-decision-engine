# Sprint 21 — Dry-Run Integration into ExecutionLoop

## Objective

Integrate the dry-run order preparation pipeline into the ExecutionLoop while preserving complete execution safety. No real orders may be submitted.

## Architecture

```
TradingSignal
     │
     ▼
DecisionPipeline.evaluate()
     │
     ▼
RiskManager.can_open_trade()
     │
     ▼
PositionSizingEngine.calculate()
     │
     ▼
[ mode == LIVE and dry_run == True ] ──YES──→ _dry_run()
     │                                            │
     NO                                           ▼
     │                                    OrderBuilder.build()
     ▼                                         │
execute()                                     ▼
(unchanged)                            PayloadValidator.validate()
                                             │
                                             ▼
                                        SignatureEngine.sign()
                                             │
                                             ▼
                                     Structured log + STOP
                                     submitted=False
```

## Execution Flow (LIVE + DRY_RUN)

1. **DecisionPipeline** — evaluate signal (unchanged)
2. **RiskManager** — gate trade (unchanged)
3. **PositionSizingEngine** — calculate size (unchanged)
4. **`ExecutionLoop._dry_run()`** — new method:
   - Calls `ExecutionRouter.prepare_order()` → routes to `LiveExecutor.prepare_order()`
   - `OrderBuilder.build()` — converts candidate + size to `PreparedOrder`
   - `PayloadValidator.validate()` — validates all fields
   - `SignatureEngine.sign()` — produces placeholder signature
   - **STOPS** — never calls `execute()`, never submits
5. **Structured logging** — single JSON log entry:

```json
{
  "event": "dry_run",
  "symbol": "BTCUSDT",
  "side": "LONG",
  "quantity": 1.0,
  "price": 50000.0,
  "client_order_id": "",
  "validation_result": true,
  "signature_present": true,
  "submitted": false
}
```

## New Config

| Name | Type | Default | Description |
|---|---|---|---|
| `DRY_RUN` | `bool` | `True` | When True and mode is LIVE, ExecutionLoop prepares but never submits |

## Modified Files

| File | Change |
|---|---|
| `config.py` | Added `DRY_RUN = True` |
| `execution/execution_loop.py` | Imported `json` and `DRY_RUN`; added `dry_run` parameter to `__init__` (defaults to config value); added `_dry_run()` method with structured logging; modified `_execute()` to check `LIVE + dry_run` before calling `execute()` |
| `execution/router.py` | Added `prepare_order()` method — routes to `LiveExecutor.prepare_order()` in LIVE mode, returns error dict in PAPER mode |

## New Files

| File | Purpose |
|---|---|
| `tests/test_execution_loop_dry_run.py` | 9 tests for dry-run behavior |

## Tests

**New tests (9):**

| Test | Verification |
|---|---|
| `test_config_dry_run_default_is_true` | `config.DRY_RUN` is `True` |
| `test_live_dry_run_calls_prepare_order_not_execute` | `prepare_order()` called exactly once, `execute()` never called |
| `test_live_dry_run_does_not_create_trade` | `process_signal()` returns `None` |
| `test_paper_mode_unchanged` | PAPER mode does not call `prepare_order()` |
| `test_live_dry_run_with_risk_block_stops_before_prepare` | Risk block stops before `prepare_order()` |
| `test_live_dry_run_rejected_pipeline_stops_early` | Pipeline rejection stops before `prepare_order()` |
| `test_prepare_order_live_mode_returns_result` | Router delegates to LiveExecutor |
| `test_prepare_order_paper_mode_returns_error` | Router returns error in PAPER mode |
| `test_prepare_order_live_no_executor_raises` | Router raises without LiveExecutor |

**All previous tests:** 153 unchanged, 0 regressions.

```
162 passed in 2.35s
```

## Safety Guarantees

- `_dry_run()` returns `None` — no trade object is ever returned to `process_signal()`, so `update_signal_status(signal.id, "EXECUTED")` is never called.
- `prepare_order()` is called instead of `execute()` — the exchange adapter's `place_order()` is never reached.
- `ExecutionRouter.prepare_order()` in PAPER mode returns an error dict — prevents accidental dry-run in PAPER.
- `DRY_RUN` defaults to `True` — safe by default.
- All new dependencies are optional in `ExecutionLoop.__init__` — existing call sites unchanged.
- Integration test (`test_integration.py`) passes unchanged — PAPER mode is completely untouched.

## Remaining Blocker

`LiveExecutor._build_payload` and `_sign_payload` (the old path used by `execute()`) are now parallel to the new `OrderBuilder` / `SignatureEngine` pipeline. A future Sprint should consolidate both paths into the new modules and deprecate the old private methods.

## Next Recommendation

**Sprint 22: Wire wallet address from environment variable.** Add `HL_WALLET_ADDRESS` to config and inject it into `LiveExecutor` as the default `address`. Then verify `LiveExecutor.monitor_open_trades()` picks it up automatically.
