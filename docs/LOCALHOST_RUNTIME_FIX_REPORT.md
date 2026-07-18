# localhost Runtime Fix Report

## Root Cause

On the developer's Windows machine, `localhost` resolves to IPv6 `::1`. The backend (`uvicorn`) listens on `0.0.0.0:8000` which binds to IPv4 `127.0.0.1` but **not** IPv6 `::1`. Therefore:

```
http://127.0.0.1:8000/health  →  HTTP 200  ✓
http://localhost:8000/health   →  ERR_CONNECTION_REFUSED  ✗
```

The frontend's `.env` had `VITE_API_URL=http://localhost:8000`, so every `fetch()` failed at the TCP level before any HTTP request was made — not a CORS or HTTP error, but a network stack failure.

## Files Modified

### `frontend/.env`

```
VITE_API_URL=http://127.0.0.1:8000
```

### `frontend/.env.example`

Updated to show `127.0.0.1` as the default and document WS derivation:

```
VITE_API_URL=http://127.0.0.1:8000
# VITE_WS_URL is derived from VITE_API_URL (http→ws) if not set
```

### `frontend/src/test/api/client.test.ts`

Updated test expectation to match new `.env` value:

```typescript
process.env.VITE_API_URL = "http://127.0.0.1:8000";
expect(BASE_URL).toBe("http://127.0.0.1:8000");
```

## Verification: Zero `localhost` occurrences

```bash
> Select-String -Pattern "localhost" frontend/**/*.ts frontend/**/*.tsx frontend/.env*
(no results)
```

All URLs are derived from a single source of truth:

| Variable | Source | Value |
|---|---|---|
| `VITE_API_URL` | `frontend/.env` | `http://127.0.0.1:8000` |
| `BASE_URL` | `api/client.ts` | `import.meta.env.VITE_API_URL` |
| `getWsBaseUrl()` | `api/client.ts` | `BASE_URL.replace(/^http/, "ws")` |
| `WS_BASE` (websocket) | `websocket/client.ts` | `getWsBaseUrl()` |
| `WS_BASE` (hooks) | `hooks/useLiveUpdates.ts` | `getWsBaseUrl()` |

**All fetch, apiFetch, WebSocket, and hook calls use these derived values.** No hardcoded hostnames exist.

## How the runtime URL flows

```
frontend/.env
  VITE_API_URL=http://127.0.0.1:8000
       │
       ▼
api/client.ts
  BASE_URL = import.meta.env.VITE_API_URL
  getWsBaseUrl() = BASE_URL.replace(/^http/, "ws")
       │                      │
       ▼                      ▼
apiFetch("/widgets/...")  new WebSocket("ws://127.0.0.1:8000/ws/...")
  fetch("http://127.0.0.1:8000/widgets/...")
```

## Test Results

All 61 tests pass across 21 test files.

## CORS Compatibility

The backend `config.py` CORS regex already matches both forms:

```
http://(localhost|127\.0\.0\.1):\d+
```

Both `localhost` and `127.0.0.1` origins are accepted — the change is purely in what the frontend *connects to*, not what the backend *accepts*.
