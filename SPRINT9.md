# Sprint 9 — Observability Foundation

Replace remaining `print()` with structured logging in 6 production files.

## Changes

### `app.py`
- Added `logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)` with structured format.
- Replaced 2 `print()` calls with `logger.critical()` / `logger.info()`.

### `core/engine.py`
- Added `logger = logging.getLogger(__name__)`
- Replaced 5 `print()` calls with `logger.info()` / `logger.exception()`.

### `core/validator.py`
- Added `logger = logging.getLogger(__name__)`
- Replaced 7 `print()` calls with `logger.info()` / `logger.error()`.
- Changed `[V]` / `[X]` checkboxes to `PASS` / `FAIL` prefix.

### `database.py`
- Added `logger = logging.getLogger(__name__)`
- Replaced 2 `print()` calls with `logger.info()` / `logger.error()`.

### `execution/trade_engine.py`
- Added `logger = logging.getLogger(__name__)`
- Replaced 2 `print()` calls with `logger.warning()` / `logger.error()`.

### `scoring/scoring_engine.py`
- Added `logger = logging.getLogger(__name__)`
- Replaced 1 `print()` call with `logger.error()`.

### `tests/conftest.py`
- Added `logging.basicConfig(level=logging.DEBUG, ...)` so test output shows structured logs.

## Stats
- **7 files changed**
- **46 insertions, 22 deletions**
- **18 `print()`→`logger.*()` replacements**
- **0 `print()` remaining in 6 target production files**
