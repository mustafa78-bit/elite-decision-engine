# Sprint 20 — Dry-Run Order Preparation Infrastructure

## Objective

Build the complete write-path infrastructure required for live trading — without submitting any orders. The system remains safe. No real exchange orders may be submitted.

## Architecture

```
TradeCandidate
     │
     ▼
OrderBuilder.build()
     │
     ▼
PreparedOrder (dataclass)
     │
     ▼
PayloadValidator.validate()
     │
     ▼
ValidationResult (dataclass)
     │
     ▼
SignatureEngine.sign()
     │
     ▼
SignedPayload (dataclass)
     │
     ▼
STOP — do NOT submit
```

The dry-run pipeline lives in `LiveExecutor.prepare_order()` and returns:

```python
{
    "ready": True,
    "validated": True,
    "signed": True,
    "submitted": False,
}
```

## Order Preparation Flow

1. **`LiveExecutor.prepare_order(candidate, size)`** — Entry point. Injects `OrderBuilder`, `PayloadValidator`, `SignatureEngine` as optional dependencies (defaults created if omitted).
2. **`OrderBuilder.build(candidate, size) → PreparedOrder`** — Converts `TradeCandidate` + `PositionSize` into a strongly typed `PreparedOrder` dataclass with `client_order_id` (new UUID), `timestamp` (ISO-8601 with tz), `notional`, and all order fields.
3. **`PayloadValidator.validate(order) → ValidationResult`** — Validates `symbol`, `side`, `order_type`, `quantity > 0`, `price > 0`, `timestamp` (ISO-8601 + tz-aware). Returns detailed per-field errors.
4. **`SignatureEngine.sign(payload) → SignedPayload`** — Compute a deterministic placeholder signature from `symbol:side:price:quantity:client_order_id:timestamp`. No real secrets, no exchange calls.

## New Files

| File | Purpose |
|---|---|
| `execution/order_builder.py` | `PreparedOrder` dataclass (frozen, 10 fields), `OrderBuilder` class |
| `execution/signature_engine.py` | `SignedPayload` dataclass (frozen, 4 fields), `SignatureEngine` class |
| `execution/payload_validator.py` | `ValidationResult` dataclass (frozen, 2 fields), `PayloadValidator` class |
| `tests/test_order_builder.py` | 9 tests — `PreparedOrder` (frozen, fields), `OrderBuilder` (build, UUID, timestamp, notional, reduce_only, TIF, short) |
| `tests/test_signature_engine.py` | 8 tests — `SignedPayload` (frozen, fields), `SignatureEngine` (sign, prefix, timestamp, uniqueness, custom signer) |
| `tests/test_payload_validator.py` | 11 tests — `ValidationResult` (valid, invalid, frozen), `PayloadValidator` (valid, empty symbol, missing symbol, invalid side, zero/negative quantity/price, missing/bad/naive timestamp, invalid order type, accumulator) |

## Modified Files

| File | Change |
|---|---|
| `execution/live_executor.py` | Added 3 imports (`OrderBuilder`, `PayloadValidator`, `SignatureEngine`), 3 new injected dependencies in `__init__`, new `prepare_order()` method with full dry-run pipeline |
| `tests/test_live_executor.py` | Added 7 `prepare_order` tests (success, bad side, zero quantity, custom builder, custom signer, no exchange call, short candidate) |

## Tests

```
153 passed in 2.39s
```

All 110 pre-existing tests pass unchanged. 43 new tests added across 6 test files.

## Safety Guarantees

- `prepare_order()` NEVER calls `exchange_adapter.place_order()`.
- `prepare_order()` NEVER calls the exchange.
- `prepare_order()` returns `{"submitted": False}` always.
- `SignatureEngine` uses `SIMULATED_SIG:` prefix placeholders — no real secrets.
- All new dependencies are optional in `LiveExecutor.__init__` — existing code paths unchanged.
- Existing `execute()` method is completely untouched.

## Remaining Blockers

1. `LiveExecutor.prepare_order()` is not yet integrated with `ExecutionLoop` — the dry-run pipeline exists but is not called during live execution passes.
2. The existing `_build_payload` / `_sign_payload` methods on `LiveExecutor` are parallel to the new pipeline — a future Sprint should consolidate them into the new modules and deprecate the old methods.

## Next Recommendation

**Sprint 21: Wire prepare_order into ExecutionLoop LIVE mode.** Replace `ExecutionLoop._execute()` call chain to route through `LiveExecutor.prepare_order()` → log result → **STOP before submit**. Add a config flag `DRY_RUN=True/False` in `config.py` that gates whether the pipeline stops after preparation or continues to `execute()`.
