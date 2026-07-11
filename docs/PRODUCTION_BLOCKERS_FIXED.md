# Production Blockers Fixed

**Date:** 2026-07-11  
**Based on:** `docs/PRODUCTION_READINESS_REPORT.md`  
**Scope:** B1, B2, B3 only  

---

## B1 — QueryClientProvider Wired (Frontend)

| Property | Before | After |
|----------|--------|-------|
| **Runtime** | All `useQuery()` calls throw `No QueryClient set` | TanStack Query properly initialized at root |
| **Verification** | `grep QueryClientProvider` returned 0 matches | Present in `main.tsx` wrapping `<App />` |

**File changed:** `frontend/src/main.tsx`

**Fix:** Added `QueryClientProvider` import from `@tanstack/react-query`, imported `queryClient` from `lib/query-client.ts`, and wrapped the app tree:

```tsx
<QueryClientProvider client={queryClient}>
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
</QueryClientProvider>
```

**Build check:** `tsc -b` — 0 errors | `vite build` — passed (624ms)

---

## B2 — `setup_logging()` Called During API Startup (Backend)

| Property | Before | After |
|----------|--------|-------|
| **Runtime** | No rotating file handlers, no JSON logging in production | 3 rotating file handlers + console handler configured at startup |
| **Verification** | `setup_logging()` defined but never called in API path | Called as first operation in `lifespan` handler |

**File changed:** `api/main.py` (line 79-80)

**Fix:** Added deferred import and call at the top of the FastAPI `lifespan` handler:

```python
from logging_config import setup_logging
setup_logging()
```

**Verification:** 4 handlers active (StreamHandler + 3 RotatingFileHandlers for engine.log, trade.log, error.log). Root logger at DEBUG level.

---

## B3 — Rate Limiting Added to Auth Endpoints (Backend)

| Property | Before | After |
|----------|--------|-------|
| **Auth endpoints** | No protection — unlimited brute-force attempts | `POST /auth/login`: 5 req/min | `POST /auth/register`: 3 req/min |
| **Libraries** | No rate limiting dependency | `slowapi` added to `requirements.txt` |

**Files changed/created:**

| File | Change |
|------|--------|
| `requirements.txt` | Added `slowapi` dependency |
| `api/rate_limit.py` | **New** — Limiter instance with 200/min default |
| `api/routes/auth.py` | Added `@limiter.limit("5/minute")` on login, `@limiter.limit("3/minute")` on register |
| `api/main.py` | Wired limiter into app state + `RateLimitExceeded` exception handler |

**Architecture:** `Limiter` uses `get_remote_address` key function (client IP). In-memory storage — no Redis dependency. Default global limit of 200 requests/minute applies to all routes.

---

## Verification Results

| Check | Result |
|-------|--------|
| `tsc -b` (TypeScript) | 0 errors |
| `vite build` | Passed (624ms) |
| `vitest run` | 21 files, 60 tests — all passed |
| Backend imports (`setup_logging`, `limiter`) | All verified |

---

## Remaining Blockers (Not Fixed)

| ID | Severity | Issue | Status |
|----|----------|-------|--------|
| **C1** | CRITICAL | Alembic migrations not configured | Awaiting CTO decision |
| **C2** | CRITICAL | Monitoring config files missing (`prometheus.yml`, Grafana dirs) | Awaiting CTO decision |
| **C3** | CRITICAL | No API-level CSP header | Awaiting CTO decision |
| **C4** | CRITICAL | No token refresh / auto-logout on JWT expiry | Awaiting CTO decision |
| **C5** | CRITICAL | No CSRF protection | Awaiting CTO decision |
| **H1** | HIGH | No frontend `.env` files | Awaiting CTO decision |
| **H2** | HIGH | No code splitting / build optimization | Awaiting CTO decision |
| **H3** | HIGH | JWT stored in `localStorage` | Awaiting CTO decision |
| **H4** | HIGH | WS token in query param | Awaiting CTO decision |
| **H5** | HIGH | DB session leak risk in routes | Awaiting CTO decision |
| **H6** | HIGH | No Sentry/error monitoring | Awaiting CTO decision |
| **H7** | HIGH | Vite config lacks build settings | Awaiting CTO decision |
| **H8** | HIGH | Redis provisioned but unused | Awaiting CTO decision |

*Full details in `docs/PRODUCTION_READINESS_REPORT.md`*
