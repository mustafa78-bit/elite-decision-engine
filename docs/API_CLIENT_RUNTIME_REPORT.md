# API Client Runtime Report

## Root Cause

The frontend had two independent environment variables for the API base URL:

```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

This duplicated configuration created a drift risk — one could change without the other. Additionally, WebSocket connections were established before authentication, causing `token=undefined` in the query string.

## Issues Found

### 1. Duplicate base URL variables

`VITE_API_URL` and `VITE_WS_URL` must be kept in sync manually. Changing the host or port requires updating both.

### 2. WebSocket connected without a token

`createSocket()` in `websocket/client.ts` always connected, even when no `auth_token` existed in localStorage. The resulting URL was:

```
ws://localhost:8000/ws/trades?token=
```

### 3. App mounted WebSocket effect before auth

`App.tsx` ran a `useEffect([], ...)` on mount that called `connectTradesSocket()`. Since the user hadn't logged in yet, the socket connected with an empty token — and never reconnected after login.

### 4. `useNotificationUpdates` captured token at render time

The hook read `localStorage.getItem("auth_token")` once at call time. If the token was absent (before login), the URL was permanently `?token=` even after the token appeared.

## Files Modified

### `api/client.ts`

Added `getWsBaseUrl()`, which derives the WebSocket URL from the HTTP base URL:

```typescript
export function getWsBaseUrl(): string {
  const override = import.meta.env.VITE_WS_URL;
  if (override) return override;
  return BASE_URL.replace(/^http/, "ws");
}
```

- `VITE_API_URL` is the single source of truth.
- `VITE_WS_URL` is still accepted as an override (backward compatible).

### `frontend/.env`

Removed `VITE_WS_URL`. Only `VITE_API_URL` is needed:

```
VITE_API_URL=http://localhost:8000
```

### `websocket/client.ts`

- Imports `getWsBaseUrl()` instead of reading `import.meta.env.VITE_WS_URL`.
- `createSocket()` guards against empty token: returns `undefined` if `getToken()` is falsy.
- All exported connect functions (`connectTradesSocket`, `connectAnalyticsSocket`, etc.) return `WebSocket | undefined`.

```typescript
function createSocket(...): WebSocket | undefined {
  const token = getToken();
  if (!token) return undefined;         // ← never sends token=undefined
  const url = `${WS_BASE}${path}?token=${encodeURIComponent(token)}`;
  ...
}
```

### `hooks/useLiveUpdates.ts`

- Imports `getWsBaseUrl()` instead of `VITE_WS_URL`.
- `useNotificationUpdates` passes an empty URL string when no token exists.
- `useLiveUpdates` skips connecting when `url` is empty:

```typescript
const connect = useCallback(() => {
  if (!url) return;                      // ← no connection attempt
  ...
}, [url, ...]);
```

### `App.tsx`

- Refactored into `App` (providers) + `AppShell` (routes + WebSocket, inside `AuthProvider` and `BrowserRouter`).
- `AppShell` uses `useAuth().isAuthenticated` and `useLocation().key` to reactively manage the trades socket:

```typescript
useEffect(() => {
  wsRef.current?.close();
  if (!isAuthenticated) return;          // ← only connect when logged in
  wsRef.current = connectTradesSocket(handler, statusHandler);
  return () => wsRef.current?.close();
}, [isAuthenticated, location.key]);
```

- The socket disconnects on logout and reconnects on login/route change.

## Verification

### All 61 frontend tests pass

```
Test Files  21 passed (21)
Tests       61 passed (61)
```

## Security

- **Never sends `token=undefined`** — WebSocket connections are completely blocked until `auth_token` exists in localStorage.
- **Backend CORS** already uses `allow_origin_regex` for flexible dev origin matching.
- **API client** already sends `Authorization: Bearer <token>` when token exists (unchanged).

## Future Considerations

- For a production deployment, the WS URL would typically be derived from the same host, so the `scheme-replace` logic holds. If a separate WS endpoint is needed, set `VITE_WS_URL` as an override.
- `useNotificationUpdates` is exported but not currently imported by any component. It remains available for future use.
