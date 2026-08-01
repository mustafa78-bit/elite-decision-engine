# Environment Variables Report

**Date:** 2026-07-11  
**Phase:** Founder Alpha | **Release:** 0.96 RC  
**Branch:** `execution-layer`

---

## Objective

Remove all hardcoded `localhost:8000` references from frontend source code. Replace with `import.meta.env.VITE_API_URL` / `import.meta.env.VITE_WS_URL` environment variables.

---

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/api/client.ts:1` | Removed `?? "http://localhost:8000"` fallback |
| `frontend/src/websocket/client.ts:9` | Removed `?? "ws://localhost:8000"` fallback |
| `frontend/src/hooks/useLiveUpdates.ts:66` | Removed `?? "ws://localhost:8000"` fallback |
| `frontend/src/test/api/client.test.ts` | Updated to use `process.env.VITE_API_URL` and dynamic imports |

---

## Changes Detail

### Before

```ts
// api/client.ts
export const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// websocket/client.ts
const WS_BASE = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";

// hooks/useLiveUpdates.ts
const WS_BASE = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";
```

### After

```ts
// api/client.ts
export const BASE_URL = import.meta.env.VITE_API_URL;

// websocket/client.ts
const WS_BASE = import.meta.env.VITE_WS_URL;

// hooks/useLiveUpdates.ts
const WS_BASE = import.meta.env.VITE_WS_URL;
```

---

## Search Results

**Grep for `localhost:8000` in `frontend/src/**/*.{ts,tsx}`:**

| File | Line | Match | Type |
|------|------|-------|------|
| `frontend/src/test/api/client.test.ts` | 3 | `process.env.VITE_API_URL = "http://localhost:8000";` | Test setup (not hardcoded) |
| `frontend/src/test/api/client.test.ts` | 8 | `expect(BASE_URL).toBe("http://localhost:8000");` | Test assertion (not hardcoded) |

**Zero hardcoded `localhost:8000` references remain in application source code.**

---

## Required Environment Variables

Applications must now be built with these env vars set:

| Variable | Example | Used In |
|----------|---------|---------|
| `VITE_API_URL` | `https://api.elite-decision.io` | `api/client.ts` — all REST API calls |
| `VITE_WS_URL` | `wss://api.elite-decision.io` | `websocket/client.ts`, `hooks/useLiveUpdates.ts` — all WebSocket connections |

### For Local Development

Create `frontend/.env.development`:

```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

Or set per-session:

```bash
# PowerShell
$env:VITE_API_URL="http://localhost:8000"
$env:VITE_WS_URL="ws://localhost:8000"
npm run dev
```

For **Vercel deployment**, set these in the Vercel dashboard under Project Settings → Environment Variables.

---

## Verification

| Check | Result |
|-------|--------|
| `grep "localhost:8000" frontend/src/**/*.ts` | ✅ 0 matches in source |
| `grep "localhost:8000" frontend/src/**/*.tsx` | ✅ 0 matches |
| `npm run build` (TypeScript + Vite) | ✅ Passed (551ms, 0 errors) |
| `npm run test` (Vitest) | ✅ 21 files / 60 tests passed |
| `BASE_URL` env test (dynamic import) | ✅ Reads from `VITE_API_URL` env var |

---

*Report generated after environment variable migration.*
