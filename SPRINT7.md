# Sprint 7 — Isolated Testing Environment

## Objective

Create an isolated testing environment where the production database is never touched by automated tests.

## Analysis

### Problem

The existing integration test (`test_integration.py` at project root) used `from database import get_session`, which connected directly to the production Postgres database defined by `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD` from `.env`. Every test run wrote test signals and trades to the production `signals` and `trades` tables.

Furthermore, the test had manual cleanup (`finally` block with `session.delete()`) that could leave orphaned rows if the test was interrupted.

### Design

Four-layer isolation:

```
                    ┌─────────────────────────────┐
                    │     test_integration.py      │
                    │    (pytest, no print())      │
                    └──────────────┬──────────────┘
                                   │ depends on
                    ┌──────────────▼──────────────┐
                    │        conftest.py          │
                    │  db_session   session_factory │
                    └──────────────┬──────────────┘
                                   │ patches
                    ┌──────────────▼──────────────┐
                    │     monkeypatch.setattr      │
                    │  database.get_session       │
                    │  execution.trade_engine.get_s │
                    │  core.engine.get_session    │
                    └──────────────┬──────────────┘
                                   │ redirects to
                    ┌──────────────▼──────────────┐
                    │       test_engine           │
                    │  TEST_DATABASE_URL (default: │
                    │  sqlite:///test_elite.db)   │
                    └─────────────────────────────┘
```

1. **`TEST_DATABASE_URL`** environment variable (default: `sqlite:///test_elite.db`)
2. **`test_engine`** fixture — session-scoped SQLAlchemy engine for the test database
3. **Automatic table cleanup** — `clean_tables` autouse fixture deletes all data after every test
4. **`monkeypatch`** — redirects every `get_session()` call site to the test database

### Mocking strategy

| Call site | File | Patch target | Mechanism |
|-----------|------|-------------|-----------|
| `update_signal_status` internal | `database.py` | `database.get_session` | `monkeypatch.setattr("database.get_session", ...)` |
| `TradeEngine.create_trade` | `execution/trade_engine.py` | `execution.trade_engine.get_session` | `monkeypatch.setattr` |
| `DecisionEngine.get_open_signals` | `core/engine.py` | `core.engine.get_session` | `monkeypatch.setattr` |
| `PaperExecutor` | `execution/paper_executor.py` | `session_factory` kwarg | Constructor injection |

## Implementation

### New files

#### `tests/__init__.py`
Empty namespace marker.

#### `tests/conftest.py` (67 lines)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `test_engine` | session | Creates SQLAlchemy engine on `TEST_DATABASE_URL`. Creates all tables once per session, drops at end. Enables SQLite WAL mode for SQLite databases. |
| `clean_tables` | function (autouse) | Deletes all data from all tables after each test. Guarantees isolation. |
| `db_session` | function | Provides a test session. Applies monkeypatches to all `get_session` call sites. |
| `session_factory` | function | Returns a callable that creates new sessions on the test engine. Used for `PaperExecutor` injection. |

#### `tests/test_integration.py` (117 lines)

Migrated from root `test_integration.py`:

| Aspect | Old (root) | New (tests/) |
|--------|-----------|--------------|
| Runner | `python test_integration.py` | `python -m pytest tests/` |
| Database | Production Postgres | `TEST_DATABASE_URL` (default: SQLite) |
| Session lifecycle | Manual open/commit/close/delete | Fixture with auto cleanup |
| PaperExecutor | Default `get_session` | Injected `session_factory` |
| Error cleanup | `try/finally` with manual delete | `clean_tables` autouse fixture |
| Output | `print()` statements | Clean pytest output |
| Assertions | 14 | 14 (same) |

### Modified files

#### `.gitignore`
Added `test_elite.db` to prevent committing generated test database files.

#### `requirements.txt`
Added `pytest` as a test dependency.

#### Deleted: `test_integration.py` (root)
Removed to prevent accidental execution against the production database.

## Validation Results

### pytest output
```
============================= test session starts ==============================
platform linux -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
tests/test_integration.py::test_end_to_end_paper_trading PASSED          [100%]
========================= 1 passed in 3.20s ====================================
```

### Isolation verification
- Test database file created: `test_elite.db` (SQLite, 24576 bytes)
- Production Postgres database: **untouched**
- Test creates and drops all tables without affecting production schema

### All assertions (14) passed

| Phase | Assertion | Status |
|-------|-----------|--------|
| Trade created | `trade is not None` | ✅ |
| Trade status | `status == "OPEN"` | ✅ |
| Trade symbol | `symbol == "BTCUSDT"` | ✅ |
| Trade side | `side == "LONG"` | ✅ |
| Trade entry | `entry == 50000.0` | ✅ |
| Trade stop | `stop == 49250.0` | ✅ |
| Trade TP1 | `tp1 == 51000.0` | ✅ |
| Trade RR | `abs(rr - 1.33) < 0.01` | ✅ |
| Signal status | `status == "EXECUTED"` | ✅ |
| Monitor found trade | `our_result is not None` | ✅ |
| Monitor detected TP | `status == "TP_HIT"` | ✅ |
| Closed status | `status == "TP_HIT"` | ✅ |
| Closed exit price | `exit_price == 52000.0` | ✅ |
| Closed reason | `close_reason == "TP_HIT"` | ✅ |

### Warning
Pandas 4.0 deprecation warning from `pandas_ta` — pre-existing, unrelated to this sprint.

## Git Diff Summary

```
 .gitignore                    |  3 ++
 requirements.txt              |  2 ++
 test_integration.py           |  1 file deleted (145 lines)
 tests/__init__.py             |  1 file (new, 0 lines)
 tests/conftest.py             |  1 file (new, 67 lines)
 tests/test_integration.py     |  1 file (new, 117 lines)
 6 files changed, 3 insertions(+), 145 deletions(-)
```

(Unrelated `SPRINT*.md`, `REVIEW.md`, `CLAUDE.md` files are untracked — documentation, not part of the sprint.)

## Remaining Blockers

- `DATABASE_URL` in `database.py` embeds the Postgres password in plaintext — should use URL construction with individual components
- The default SQLite test database does not support `DateTime(timezone=True)` — use `TEST_DATABASE_URL=postgresql://...` for full compatibility
- `test_elite.db` is created in the project root — could collide with version control if `.gitignore` is not respected
- No `pytest.ini` or `pyproject.toml` configuration — `python -m pytest tests/` must be run from the project root

## Next Recommendation

1. Add a `pytest.ini` or `pyproject.toml` section for pytest configuration (test path, markers, etc.)
2. Extract `MockCollector` and `MockScoringEngine` into `tests/mocks.py` for reuse across test files
3. Convert the 8 legacy smoke tests (root `test_*.py`) to pytest with assertions
4. Add a CI workflow (`github/workflows/test.yml`) that runs `pytest tests/` with `TEST_DATABASE_URL`
