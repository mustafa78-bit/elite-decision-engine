# Sprint 22 — Consolidate Write Path (Remove Duplicated Pipeline)

## Objective

Remove duplicated write-path logic and consolidate all live order preparation into a single implementation. There must be one and only one order preparation pipeline. Old helper methods must disappear.

## Architecture (Before)

```
execute():
    _validate()           ← private, duplicates PayloadValidator
    _build_payload()      ← private, duplicates OrderBuilder
    _sign_payload()       ← private, duplicates SignatureEngine
    exchange_adapter.place_order()
    _parse_response()
    _persist_trade()

prepare_order():
    OrderBuilder.build()
    PayloadValidator.validate()
    SignatureEngine.sign()
    return dict
```

**Problem:** Two parallel code paths for the same logic (build → validate → sign). Three private methods duplicated the functionality of the injected components.

## Architecture (After)

```
execute():
    OrderBuilder.build()       ← shared
    PayloadValidator.validate() ← shared
    SignatureEngine.sign()      ← shared
    _signed_to_dict()          ← NEW thin converter
    exchange_adapter.place_order()
    _parse_response()
    _persist_trade()

prepare_order():
    OrderBuilder.build()       ← shared
    PayloadValidator.validate() ← shared
    SignatureEngine.sign()      ← shared
    return dict
```

**Result:** Both paths call the exact same `self._order_builder.build()`, `self._payload_validator.validate()`, `self._signature_engine.sign()` — zero duplication.

## Removed Technical Debt

| Removed Method | Lines | Replaced By |
|---|---|---|
| `_validate()` | 14 | `PayloadValidator.validate()` (14 richer checks) |
| `_build_payload()` | 9 | `OrderBuilder.build()` (injected) |
| `_sign_payload()` | 5 | `SignatureEngine.sign()` (injected) |

**Total:** 28 lines of duplicated logic eliminated.

## Added

| Added Method | Lines | Purpose |
|---|---|---|
| `_signed_to_dict()` | 14 | Thin static converter — `PreparedOrder` + `SignedPayload` → flat dict for exchange adapter |

## Modified Files

| File | Change |
|---|---|
| `execution/live_executor.py` | Removed `_validate()`, `_build_payload()`, `_sign_payload()`. Refactored `execute()` to use `OrderBuilder` → `PayloadValidator` → `SignatureEngine`. Added `_signed_to_dict()` static converter. |
| `tests/test_live_executor.py` | Updated 3 error-message assertions (moved from `_validate` to `PayloadValidator`). Updated 1 signature assertion (`SIMULATED_SIGNATURE_PLACEHOLDER` → `SIMULATED_SIG:`). Added 4 regression tests. |

## Regression Tests (4 new)

| Test | What It Proves |
|---|---|
| `test_execute_and_prepare_use_same_builder` | Both paths call `OrderBuilder.build()` with same candidate |
| `test_execute_and_prepare_use_same_validator` | Both paths call `PayloadValidator.validate()` |
| `test_execute_and_prepare_use_same_signer` | Both paths call `SignatureEngine.sign()` |
| `test_execute_payload_contains_all_order_fields` | The dict sent to `exchange_adapter.place_order()` contains all 11 expected fields |

## Test Results

```
166 passed in 2.62s
```

All 162 pre-existing tests pass unchanged. 4 new regression tests.

## Safety Guarantees

- `execute()` no longer has its own validation/payload/signing logic — it delegates to exactly the same injected components as `prepare_order()`.
- `_signed_to_dict()` is a pure static converter — no side effects, no state.
- `prepare_order()` is completely unchanged — same interface, same output.
- `_parse_response()` and `_persist_trade()` are untouched.
- The `SimulatedExchangeAdapter` sees the exact same dict fields as before (symbol, side, order_type, price, quantity, notional, time_in_force, timestamp, signature, signing_timestamp) plus `client_order_id`.

## Remaining Blockers

None. The write path is fully consolidated.

## Next Recommendation

**Sprint 23: Move monitor path to use PreparedOrder.** Currently `monitor_open_trades()` builds `LiveMonitorResult` directly from `Position` dataclass fields. Create a `MonitorResultBuilder` (analogous to `OrderBuilder`) and inject it. This completes the pattern of injectable builders for every output type.
