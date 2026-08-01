# CORS Runtime Fix Report

## Root Cause

The frontend Vite dev server runs at `http://127.0.0.1:5173`, but the backend's CORS configuration only allowed `http://localhost:5173`. Although `127.0.0.1` and `localhost` resolve to the same machine, browsers treat them as **different origins** for CORS purposes. Every cross-origin request from `http://127.0.0.1:5173` was blocked because the `Access-Control-Allow-Origin` header was not returned.

## Files Modified

### `config.py` (line 53)

**Before:**
```python
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
```

**After:**
```python
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
```

## Why This Fix Is Production-Safe

- In production, `CORS_ORIGINS` is set via environment variable to the production domain(s).
- The change only affects the **development default** fallback when the env var is not set.
- Authentication remains fully enabled. No security was relaxed.
- The `CORS_ORIGINS` env var takes precedence in all environments via `os.getenv()`.

## Verification

### 1. Server Boot
```bash
python -m uvicorn api.main:app --port 8000
```
Result: Server starts successfully.

### 2. Health Check
```bash
GET /health
```
Result: HTTP 200, `{"status":"ok", ...}`

### 3. CORS — OPTIONS Preflight
```http
OPTIONS /auth/login
Origin: http://127.0.0.1:5173
Access-Control-Request-Method: POST
```
Result: HTTP 200
```
Access-Control-Allow-Origin: http://127.0.0.1:5173
Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Credentials: true
Vary: Origin
```

### 4. CORS — Simple Request (POST)
```http
POST /auth/login
Origin: http://127.0.0.1:5173
```
Result: HTTP 200
```
Access-Control-Allow-Origin: http://127.0.0.1:5173
Access-Control-Allow-Credentials: true
```

### 5. CORS — Both Origins Verified
Both `http://localhost:5173` and `http://127.0.0.1:5173` return the correct `Access-Control-Allow-Origin` header matching the request origin.

## Final Result

- Frontend at `http://127.0.0.1:5173` can now make authenticated requests to `http://localhost:8000`.
- CORS preflight (OPTIONS) succeeds.
- WebSocket connections at `ws://localhost:8000/ws/*` will connect after successful login.
- No production configuration was altered. No security was reduced.
