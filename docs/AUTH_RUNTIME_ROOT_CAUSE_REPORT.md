# Auth Runtime Root Cause Report

## Symptoms

1. **Widgets return 401 Unauthorized** — `Authorization: Bearer undefined` sent to backend.
2. **WebSocket URL: `ws://127.0.0.1:8000/ws/trades?token=undefined`** — literal string `"undefined"` as the token.
3. **Dashboard renders despite invalid auth** — `AuthGuard` finds truthy value in localStorage.

## Root Cause

`localStorage.setItem("auth_token", undefined)` stores the **string** `"undefined"` because `localStorage` silently converts non-string values via `String()`.

The string `"undefined"` is **truthy**, so every `if (token)` check passes:
- `AuthGuard` → finds `"undefined"` → renders dashboard
- `getAuthHeaders()` → returns `Authorization: Bearer undefined` → backend returns 401
- `getToken()` → returns `"undefined"` → WebSocket URL: `?token=undefined`

## Code Path

```
LoginPage.tsx:22  ← root cause
  localStorage.setItem("auth_token", res.token)
                          res.token is undefined → stores STRING "undefined"
                                │
                  ┌─────────────┼──────────────┐
                  ▼             ▼               ▼
           AuthGuard.tsx    api/client.ts   websocket/client.ts
           "undefined"      "undefined"     "undefined"
           is truthy        is truthy       is truthy
           → renders        → sends         → connects
             dashboard        Bearer          with
                              undefined       token=undefined
                              401              rejected
```

### How `undefined` enters localStorage

`LoginPage.tsx` (before fix) called `apiFetch` directly and stored `res.token` without validation:

```typescript
const res = await apiFetch<{ token: string }>("/auth/login", ...);
localStorage.setItem("auth_token", res.token);  // res.token could be undefined
```

If the API response had no `token` field, or if the response parsing failed silently, `res.token` evaluated to JavaScript `undefined`. `localStorage.setItem` converted it to the string `"undefined"`.

**Once `"undefined"` is in localStorage, it persists across page loads and survives login/logout cycles** because:
- Login overwrites it with... `"undefined"` again (same bug path)
- Logout uses `removeItem` (which does work, but only if explicitly called)
- The string `"undefined"` is never treated as invalid

### Secondary issue: LoginPage bypasses AuthProvider

Even when login succeeds with a valid token, `LoginPage` wrote directly to localStorage instead of calling `AuthProvider.login()`. This meant:

1. `AuthProvider`'s React state (`token`, `isAuthenticated`) was **never updated** after login
2. `AppShell`'s `useAuth().isAuthenticated` remained `false`
3. The WebSocket effect (guarded by `if (!isAuthenticated) return;`) **never established the trades socket**
4. `ConnectionStatusBadge` always showed "Offline"

`AuthGuard` (which reads localStorage directly) found the token, so the dashboard rendered — but with no WebSocket connection and stale auth state.

## Files Modified

### 1. `api/client.ts` — exported `isValidToken()`, validated in `getAuthHeaders()`

```typescript
export function isValidToken(t: string | null | undefined): boolean {
  return !!t && t !== "undefined" && t !== "null";
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("auth_token");
  return isValidToken(token) ? { Authorization: `Bearer ${token}` } : {};
}
```

**Effect:** Rejects `"undefined"` and `"null"` strings. Never sends `Authorization: Bearer undefined`.

### 2. `websocket/client.ts` — validated token in `getToken()`

```typescript
function getToken(): string {
  const t = localStorage.getItem("auth_token");
  return isValidToken(t) ? t : "";
}
```

**Effect:** Returns `""` for invalid tokens → `createSocket` returns `undefined` → WebSocket never connects without a real token.

### 3. `hooks/useLiveUpdates.ts` — validated token

```typescript
const raw = localStorage.getItem("auth_token");
const token = isValidToken(raw) ? raw : "";
```

**Effect:** Same protection in notification updates hook.

### 4. `AuthProvider.tsx` — validated token init + login error propagation

**Initialization:**
```typescript
const [token, setToken] = useState<string | null>(() => {
  const t = localStorage.getItem("auth_token");
  return isValidToken(t) ? t : null;
});
```

**Login:**
```typescript
const login = useCallback(async (username: string, password: string) => {
  setIsLoading(true);
  try {
    const res = await apiFetch<{ token: string }>("/auth/login", { ... });
    if (!res.token || !isValidToken(res.token)) {
      throw new Error("Invalid token received");
    }
    setToken(res.token);
    ...
  } catch (err) {
    setIsLoading(false);
    throw err;  // ← propagated to LoginPage
  }
  setIsLoading(false);
}, []);
```

**Effect:** Invalid tokens rejected at initialization. Login errors propagate to caller. Token validated before storing.

### 5. `AuthGuard.tsx` — validated token

```typescript
const raw = localStorage.getItem("auth_token");
if (!isValidToken(raw)) {
  return <Navigate to="/login" replace />;
}
```

**Effect:** Dashboard never renders with `"undefined"` or `"null"` tokens. Always redirects to `/login`.

### 6. `LoginPage.tsx` — uses `AuthProvider.login()` instead of direct `apiFetch`

```typescript
import { useAuth } from "../components/auth/AuthProvider";

const { login: authLogin } = useAuth();

async function handleSubmit(e: React.FormEvent) {
  e.preventDefault();
  setLoading(true);
  try {
    await authLogin(username, password);
    addGlobalToast("Logged in successfully", "success");
    navigate("/dashboard");
  } catch {
    addGlobalToast("Invalid credentials", "error");
  } finally {
    setLoading(false);
  }
}
```

**Effect:** AuthProvider React state is updated after login. `AppShell`'s `useAuth().isAuthenticated` becomes `true`. WebSocket connects. No more direct `localStorage.setItem`.

## How the auth flow works after fixes

```
LoginPage
  └─ useAuth().login(username, password)
       └─ AuthProvider.login()
            ├─ apiFetch("/auth/login") → { token: "jwt..." }
            ├─ validates token (isValidToken)
            ├─ setToken(jwt)  ← updates React state
            ├─ localStorage.setItem("auth_token", jwt)
            └─ returns (success)

AppShell
  └─ useAuth().isAuthenticated → true
       └─ useEffect → connectTradesSocket()
            └─ createSocket("/ws/trades")
                 ├─ getToken() → "jwt..." (valid)
                 ├─ new WebSocket("ws://...?token=jwt...")
                 └─ statusHandler("CONNECTED")
                      └─ setWsRooms({ ...trades: "CONNECTED" })
                           └─ ConnectionStatusBadge → "Live"

Dashboard
  └─ apiFetch("/widgets/kpi/detail")
       ├─ getAuthHeaders() → { Authorization: "Bearer jwt..." }
       └─ fetch("http://127.0.0.1:8000/widgets/kpi/detail", ...)
            └─ backend → 200 { kpis: [...] }
```

## Defense-in-depth

Every path that reads `auth_token` from localStorage now validates via `isValidToken()`:

| Consumer | Before | After |
|---|---|---|
| `api/client.ts` (HTTP auth) | `token ? ...` | `isValidToken(token) ? ...` |
| `websocket/client.ts` (WS auth) | `t ?? ""` then `!t` check | `isValidToken(t) ? t : ""` |
| `hooks/useLiveUpdates.ts` (WS notifications) | `token ? ...` | `isValidToken(raw) ? raw : ""` |
| `AuthProvider.tsx` (React state init) | `localStorage.getItem(...)` | `isValidToken(t) ? t : null` |
| `AuthGuard.tsx` (route guard) | `!token` | `!isValidToken(raw)` |
| `LoginPage.tsx` (token storage) | `setItem("auth_token", res.token)` | Uses `AuthProvider.login()` (validates) |

## Test Results

All 61 tests pass across 21 test files.
