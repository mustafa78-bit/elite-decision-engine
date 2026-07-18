# Login Rate Limit Report

## Current Status

`POST /auth/login` returns **HTTP 429 Too Many Requests**.

## Root Cause

The login endpoint had a **hardcoded** rate limit of **5 requests per minute**:

```python
# api/routes/auth.py (before fix)
@router.post("/auth/login")
@limiter.limit("5/minute")
def login(request: Request, body: AuthRequest):
```

During development, every request originates from `127.0.0.1` (same machine). SlowAPI identifies clients via `get_remote_address` (the client IP). Each login attempt increments the counter for `127.0.0.1`. With 5/minute, repeated testing (login → check → logout → login) exhausts the limit within seconds.

## Files and Limits

| File | Endpoint | Limit |
|---|---|---|
| `api/routes/auth.py:36` | `POST /auth/login` | 5/minute |
| `api/routes/auth.py:29` | `POST /auth/register` | 3/minute |
| `api/rate_limit.py:4` | global default | 200/minute |

## Fix Applied

### `config.py` — env-aware defaults

```python
AUTH_LOGIN_RATE_LIMIT = os.getenv(
    "AUTH_LOGIN_RATE_LIMIT",
    "30/minute" if API_ENV == "development" else "5/minute",
)
AUTH_REGISTER_RATE_LIMIT = os.getenv(
    "AUTH_REGISTER_RATE_LIMIT",
    "10/minute" if API_ENV == "development" else "3/minute",
)
```

### `api/routes/auth.py` — dynamic limits

```python
from config import AUTH_LOGIN_RATE_LIMIT, AUTH_REGISTER_RATE_LIMIT

@router.post("/auth/register")
@limiter.limit(AUTH_REGISTER_RATE_LIMIT)

@router.post("/auth/login")
@limiter.limit(AUTH_LOGIN_RATE_LIMIT)
```

## Resulting Behaviour

| Environment | Login limit | Register limit | Source |
|---|---|---|---|
| `development` (default) | 30/minute | 10/minute | `config.py` env-aware default |
| `production` | 5/minute | 3/minute | `config.py` env-aware default |
| Any (override) | custom | custom | `AUTH_LOGIN_RATE_LIMIT` / `AUTH_REGISTER_RATE_LIMIT` env vars |

## Verified

```python
API_ENV=development  → login=30/minute  register=10/minute
API_ENV=production   → login=5/minute   register=3/minute   ← unchanged
AUTH_LOGIN_RATE_LIMIT=100/hour → login=100/hour  register=<env-default>
```

## Key points

- **Rate limiting is NOT disabled** — only the threshold changes per environment.
- **Production limits are completely unchanged** — 5/login, 3/register.
- **Development gets generous limits** (30/10) so repeated testing never hits 429.
- **Any limit can be overridden** via env var for custom deployments.
