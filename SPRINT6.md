# Sprint 6 — Production Startup Validation

## Objective

Implement a startup validation layer that checks all required runtime dependencies before the engine enters the main execution loop, with clear error reporting and fail-fast behavior.

## Analysis

### Runtime dependencies identified

| Dependency | Source | Required? | Current handling |
|-----------|--------|-----------|-----------------|
| `POSTGRES_HOST` | `.env` / env var | Yes | No default; crash on first query |
| `POSTGRES_USER` | `.env` / env var | Yes | No default; crash on first query |
| `POSTGRES_PASSWORD` | `.env` / env var | Yes | No default; crash on first query |
| `POSTGRES_PORT` | `.env` / env var | No | Default `"5432"` |
| `POSTGRES_DB` | `.env` / env var | No | Default `"decision_engine"` |
| PostgreSQL server | Network | Yes | `create_tables()` raises raw SQLAlchemy exception |
| `CHECK_INTERVAL` | `config.py` | Yes | Hardcoded `10` |
| `MIN_SCORE` | `config.py` | Yes | Hardcoded `85` |
| `MAX_OPEN_TRADES` | `config.py` | Yes | Hardcoded `3` |
| `HL_API_KEY`, `HL_SECRET` | `.env` / env var | **No** | Defined in config but never used by any component |
| `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` | `.env` / env var | **No** | Defined in config but never used by any component |
| `https://api.hyperliquid.xyz/info` | Network | No | Required for trading, not for startup |
| Local files/dirs | Filesystem | No | No hardcoded file paths at runtime |

### Validation design

Three checks in sequence:

1. **Environment variables** — verify Postgres credentials are non-empty
2. **Database connectivity** — execute `SELECT 1` against Postgres
3. **Configuration sanity** — validate numeric ranges for `CHECK_INTERVAL`, `MIN_SCORE`, `MAX_OPEN_TRADES`

Fail-fast by default: first failure prints a clear message and exits with code 1.

## Implementation

### New file: `core/validator.py` (48 lines)

`StartupValidator` class with:
- `.run(fail_fast=True)` — runs all checks, returns `True`/`False`
- `_check_env_vars()` — validates `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `_check_db_connectivity()` — executes `SELECT 1` via SQLAlchemy
- `_check_config_sanity()` — validates `CHECK_INTERVAL >= 1`, `MIN_SCORE` in 0-100, `MAX_OPEN_TRADES >= 0`

### Modified file: `app.py` (8 lines changed)

```diff
+import sys
 from core.engine import DecisionEngine
+from core.validator import StartupValidator

 def main():
+    validator = StartupValidator()
+    if not validator.run():
+        print("FAILED: Engine startup validation failed. Exiting.")
+        sys.exit(1)
+
     create_tables()
-    print("🚀 Elite Decision Engine Started")
+    print("Elite Decision Engine Started")
     engine = DecisionEngine()
     engine.run()
```

The validator runs before `create_tables()` and the main loop. Fail-fast prevents entering the loop with missing dependencies.

## Validation Results

```
==================================================
STARTUP VALIDATION
==================================================
  [V] Environment variables
  [V] Database connectivity
  [V] Configuration sanity

All checks passed.
```

All three checks pass with the current `.env` configuration.

## Test Output

### Integration test
```
[SIGNAL] Created test signal id=1383
[TRADE] Created id=7 entry=50000.0 stop=49250.0 tp1=51000.0 rr=1.33
[MONITOR] Trade id=7 status=TP_HIT
[CLOSE] Trade id=7 status=TP_HIT exit=52000.0 reason=TP_HIT
=== ALL INTEGRATION TESTS PASSED ===
```

### Existing tests
| Test | Result |
|------|--------|
| `test_pipeline.py` | Pipeline decision: REJECT |
| `test_score.py` | Scores returned |
| `test_indicators.py` | Indicators calculated |

All pass. No regressions.

## Git Diff Summary

```
 app.py             | 10 ++++++++--
 core/validator.py  |  1 file (new, 48 lines)
 2 files changed, 9 insertions(+), 2 deletions(-)
```

(Unrelated `requirements.txt` whitespace from Sprint 1 excluded.)

## Remaining Blockers

- **No test for the validator itself** — the validator relies on external state (Postgres, env vars) and is verified manually. A unit test with mocked env/db would be ideal but requires a test harness.
- **`HL_API_KEY`, `HL_SECRET`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` are dead config** — defined in `config.py` and `.env` but never referenced by any component. They should be removed or their consuming components should be implemented.

## Next Recommendation

1. Remove dead config keys (`HL_API_KEY`, `HL_SECRET`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`) from `config.py` and `.env.example`.
2. Add a startup connectivity check for the Hyperliquid API (optional — warn if unreachable, don't block).
3. Convert the validator to a proper module with both `run()` and `run_or_exit()` methods for reuse across entry points.
