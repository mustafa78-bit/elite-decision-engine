# Sprint 3 — Duplicate `update_signal_status` Fix

## Objective

Remove the duplicate `update_signal_status` implementation in `database.py` and keep the `get_session()`-based version as the single source of truth.

## Implementation

**File:** `database.py`

Two changes:

1. **Deleted** the first definition (lines 143-162) — the `get_session()`-based version that was dead code (overwritten at module load).
2. **Changed** the remaining definition (line 152): `session = SessionLocal()` → `session = get_session()`.

The remaining definition now uses `get_session()` for consistency with the rest of the codebase. No behavioral change — `get_session()` is `def get_session(): return SessionLocal()`.

```diff
-def update_signal_status(signal_id, new_status):
-    session = get_session()
-    try:
-        ...
-    finally:
-        session.close()
-
-# ------------------------------------------------------------------
-# INIT
-# ------------------------------------------------------------------
-
 if __name__ == "__main__":
     create_tables()
     print("Database initialized successfully.")

 def update_signal_status(signal_id, new_status):
-    session = SessionLocal()
+    session = get_session()
```

## Test Output

### `test_pipeline.py`
```
Pipeline decision for BTCUSDT LONG 1h: REJECT
REJECTED
```

### `test_score.py`
```
{...'final_score': 0.63...}
```

### `test_indicators.py`
```
{...'atr': 421.2240651035099...}
```

All tests pass. No regressions.

## Git Diff Summary

- `database.py`: -1 definition (20 lines removed), +1 line changed (`SessionLocal()` → `get_session()`)
- `requirements.txt`: Unrelated whitespace change from Sprint 1 (not this sprint)

Net change: **20 lines removed, 1 line modified**.

## Remaining Backlog

- Dead code removal (unused imports in various files)
- Unused dependencies in `requirements.txt` (fastapi, uvicorn, numpy, tenacity, websocket-client, colorlog)
- Startup validation for database connectivity
- `database.py`: the second `update_signal_status` definition still sits after the `if __name__ == "__main__"` guard block — cosmetic cleanup only, no behavioral impact
