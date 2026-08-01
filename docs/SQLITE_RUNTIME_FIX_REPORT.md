# SQLite Runtime Fix Report

## Root Cause

The backend always defaulted to PostgreSQL because `config.py:37-50` falls back to a PostgreSQL connection string when `DATABASE_URL` is not set:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    if not POSTGRES_HOST:
        POSTGRES_HOST = "localhost"
    ...
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{POSTGRES_HOST}:{DB_PORT}/{DB_NAME}"
```

Since `DATABASE_URL` was not defined in `.env` (which only had `JWT_SECRET`), every database operation attempted to connect to `postgresql://postgres:postgres@localhost:5432/decision_engine`. With no PostgreSQL server running locally, connections failed, causing HTTP 500 on every endpoint that accessed the database.

## Fix 1 — `.env` (line 2)

Added SQLite connection string for local development:

```
DATABASE_URL=sqlite:///test_elite.db
```

This is picked up by `config.py:5` (`load_dotenv()`) and used directly at line 37, bypassing the PostgreSQL fallback entirely. `.env` is in `.gitignore`, so this never affects production.

## Fix 2 — `database.py` (lines 22-28)

Added SQLite-compatible engine settings. PostgreSQL pools of size 10 with 20 overflow are inappropriate for SQLite:

```python
_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=not _is_sqlite,
    pool_size=1 if _is_sqlite else 10,
    max_overflow=0 if _is_sqlite else 20,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)
```

Key changes for SQLite:
- `pool_size=1` — SQLite does not benefit from connection pools
- `max_overflow=0` — prevents connection accumulation
- `check_same_thread=False` — allows SQLAlchemy to use the connection across threads (required by FastAPI's async handling)

## Files Modified

| File | Change |
|---|---|
| `.env` | Added `DATABASE_URL=sqlite:///test_elite.db` |
| `database.py` | Added SQLite-compatible engine configuration |

## Verification

### GET /health
```http
GET /health
```
```json
{"status":"ok","service":"elite-decision-engine","env":"development","uptime_seconds":9.08}
```
Result: HTTP 200 ✅

### POST /auth/register
```http
POST /auth/register
Content-Type: application/json

{"username":"admin","email":"admin@test.com","password":"password123"}
```
```json
{"success":true,"token":"eyJ...","user":{"id":1,"username":"admin","email":"admin@test.com"}}
```
Result: HTTP 200 ✅

### POST /auth/login (valid)
```http
POST /auth/login
Content-Type: application/json

{"username":"admin","password":"password123"}
```
```json
{"success":true,"token":"eyJ...","user":{"id":1,"username":"admin","email":"admin@test.com"}}
```
Result: HTTP 200 ✅

### POST /auth/login (invalid password)
```http
POST /auth/login
Content-Type: application/json

{"username":"admin","password":"wrong"}
```
```json
{"success":false,"error":"Invalid username or password"}
```
Result: HTTP 200 ✅

### POST /auth/login (nonexistent user)
```http
POST /auth/login
Content-Type: application/json

{"username":"test","password":"test"}
```
```json
{"success":false,"error":"Invalid username or password"}
```
Result: HTTP 200 ✅

## Result

No HTTP 500 errors. All database operations use the local SQLite file `test_elite.db`. Local development no longer requires a running PostgreSQL instance.
