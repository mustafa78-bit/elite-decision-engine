# Frontend Auth Fix Report

## Root Cause

The CORSMiddleware was registered **before** the `@app.middleware("http")` decorators in `api/main.py`. Starlette's `add_middleware` uses `insert(0, ...)` (prepend), which caused CORSMiddleware to become the **innermost** middleware. The auth middleware ran **before** CORS, rejecting every OPTIONS preflight with 401 before CORSMiddleware could respond with the correct CORS headers.

Without a successful preflight, the browser refuses to send the `Authorization` header on actual requests — so every authenticated API call arrived at the backend without a token, resulting in a 401.

## Middleware Order (Before)

```
Registration:  [CORSMiddleware, auth_middleware, security_headers]
                      ↓  (add_middleware prepends)
user_middleware: [security_headers, auth_middleware, CORSMiddleware]
                      ↓  (build_middleware_stack reverses)
Execution:  security_headers → auth_middleware → CORSMiddleware → router
                                              ↑
                              Auth rejects OPTIONS preflight here
```

## Fix Applied — `api/main.py`

Moved `app.add_middleware(CORSMiddleware, ...)` from **before** the `@app.middleware("http")` decorators to **after** them.

### Before (line ~135)
```python
app.add_middleware(CORSMiddleware, ...)   # added FIRST → ends up innermost
app.middleware("http")(auth_middleware)
@app.middleware("http")
async def security_headers_middleware(...): ...
```

### After (line ~151)
```python
app.middleware("http")(auth_middleware)
@app.middleware("http")
async def security_headers_middleware(...): ...

app.add_middleware(CORSMiddleware, ...)   # added LAST → ends up outermost
```

### Middleware Order (After)

```
Registration:  [auth_middleware, security_headers, CORSMiddleware]
                      ↓  (prepend)
user_middleware: [CORSMiddleware, security_headers, auth_middleware]
                      ↓  (reverse)
Execution:  CORSMiddleware → security_headers → auth_middleware → router
                ↑
    CORS intercepts OPTIONS preflight here
```

## Verification

### 1. OPTIONS Preflight (was failing, now succeeds)
```http
OPTIONS /widgets/kpi/detail
Origin: http://127.0.0.1:5173
Access-Control-Request-Method: GET
Access-Control-Request-Headers: authorization, content-type
```
**Before:** HTTP 401 (auth middleware rejected before CORS could respond)
**After:** HTTP 200
```
Access-Control-Allow-Origin: http://127.0.0.1:5173
Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: authorization, content-type
Access-Control-Allow-Credentials: true
Vary: Origin
```

### 2. Login
```http
POST /auth/login
Content-Type: application/json

{"username":"admin","password":"password123"}
```
Result: HTTP 200, token returned

### 3. Authenticated API Request
```http
GET /widgets/kpi/detail
Authorization: Bearer <token>
Origin: http://127.0.0.1:5173
```
Result: HTTP 200, KPI data returned with `Access-Control-Allow-Origin: http://127.0.0.1:5173`

## File Changed

| File | Change |
|---|---|
| `api/main.py` | Moved `app.add_middleware(CORSMiddleware, ...)` after the `@app.middleware("http")` decorators |

## Why the Frontend Auth Flow Now Works

1. **Login stores JWT** — `LoginPage.tsx` calls `apiFetch("POST /auth/login")`, stores `res.token` in `localStorage("auth_token")`.
2. **Authorization header sent** — `api/client.ts:getAuthHeaders()` reads `auth_token` from localStorage and injects `Authorization: Bearer <token>` on every request.
3. **Dashboard redirects if no token** — `AuthGuard.tsx` checks `localStorage("auth_token")` and redirects to `/login` if missing.
4. **CORS preflight succeeds** — Browser sends OPTIONS → CORSMiddleware returns 200 with `Access-Control-Allow-Headers: authorization` → browser allows the `Authorization` header on the actual request.
5. **Backend validates token** — Auth middleware sees the `Authorization: Bearer <token>` header, decodes the JWT, and allows the request through.

No frontend code changes were needed. The auth flow was already correct on the frontend — the issue was entirely backend CORS middleware ordering.
