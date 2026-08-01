# Production Readiness Report

**Date:** 2026-07-11  
**Auditor:** AI Agent (Founder Mode)  
**Release:** 0.96 RC | Phase: Founder Alpha  
**Branch:** `execution-layer`

---

## Scope

Full production-readiness audit of the Elite Decision Engine — frontend, backend, deployment, security, monitoring, and infrastructure. No new features introduced.

---

## Severity Key

| Label | Meaning |
|-------|---------|
| **BLOCKER** | Prevents successful production deployment |
| **CRITICAL** | Severe production risk; must fix before launch |
| **HIGH** | Significant risk or operational gap |
| **MEDIUM** | Important but not blocking |
| **LOW** | Non-critical improvement |

---

## BLOCKER Items

### B1 — `QueryClientProvider` Not Wired (Frontend)

| Property | Value |
|----------|-------|
| **File** | `frontend/src/main.tsx` (missing) |
| **Severity** | BLOCKER |
| **Risk** | Runtime crash when any component using `@tanstack/react-query` mounts |
| **Evidence** | `lib/query-client.ts` exports a `queryClient` instance, but **no `QueryClientProvider` wraps the component tree** in `main.tsx`, `App.tsx`, or anywhere else. 6+ dashboard widgets and all 8 `hooks/queries.ts` hooks call `useQuery()` — every one will throw `No QueryClient set` at render time. |
| **Fix** | Wrap `<App />` in `<QueryClientProvider client={queryClient}>` inside `main.tsx`. |

### B2 — `setup_logging()` Never Called (Backend)

| Property | Value |
|----------|-------|
| **File** | `logging_config.py` (defined line 59, never called) |
| **Severity** | BLOCKER |
| **Risk** | No rotating file logs, no JSON-structured logging in production; all log output goes to stderr with default Python formatting |
| **Evidence** | `setup_logging()` is defined in `logging_config.py` (configures 3 rotating file handlers + JSON console in production) but is **never called** after import. The only consumer is `app.py:12` (CLI entry point). The API lifespan in `api/main.py` (lines 74–90) does not call it. Tests call it in `conftest.py:28`. |
| **Fix** | Call `setup_logging()` at the very start of the FastAPI `lifespan` handler in `api/main.py` before any loggers are used. |

### B3 — Rate Limiting Not Implemented (Backend)

| Property | Value |
|----------|-------|
| **File** | `api/main.py`, `api/middleware.py` |
| **Severity** | BLOCKER |
| **Risk** | No protection against brute-force login attacks, API abuse, or DoS |
| **Evidence** | `POST /auth/login` has zero rate limiting. An attacker can submit unlimited password guesses. No `slowapi` or similar library in `requirements.txt`. No custom middleware for rate limiting. The `LAUNCH_CHECKLIST.md` lists this as checked (`[x]`) but the code does not implement it. |
| **Fix** | Add `slowapi` dependency and middleware, or implement custom token-bucket/IP-based rate limiting, especially on `/auth/login` and `/auth/register`. |

---

## CRITICAL Items

### C1 — No Schema Migration System (Backend)

| Property | Value |
|----------|-------|
| **File** | `database.py:243` (`Base.metadata.create_all()`) |
| **Severity** | CRITICAL |
| **Risk** | Any schema change requires manual DDL or full table recreation. No rollback capability. No migration history. |
| **Evidence** | Tables are created imperatively via `Base.metadata.create_all(bind=engine)`. No `alembic.ini`, no `migrations/` directory, no Alembic dependency in `requirements.txt`. |
| **Fix** | Initialize Alembic (`alembic init migrations`), generate an initial migration, and replace `create_tables()` with `alembic upgrade head` in the startup sequence. |

### C2 — Monitoring Config Files Missing (Infra)

| Property | Value |
|----------|-------|
| **File** | `docker-compose.prod.yml` references non-existent files |
| **Severity** | CRITICAL |
| **Risk** | `docker-compose.prod.yml up` will fail because Prometheus and Grafana config files do not exist |
| **Evidence** | Lines 109, 121–122 reference `./monitoring/prometheus.yml`, `./monitoring/grafana-dashboards/:ro`, `./monitoring/grafana-datasources/:ro`. **None of these files or directories exist.** |
| **Fix** | Create stub Prometheus config, Grafana dashboard/datasource provisioning files, or remove Prometheus/Grafana from production compose until ready. |

### C3 — No API-Level Content-Security-Policy (Backend)

| Property | Value |
|----------|-------|
| **File** | `api/main.py:136-146` |
| **Severity** | CRITICAL |
| **Risk** | CSP is set in nginx (serving the frontend SPA) and in `frontend/index.html`, but the **API responses lack CSP headers**. XSS via API responses is not mitigated at the API boundary. |
| **Evidence** | The `security_headers_middleware` (line 136) sets `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, and `Strict-Transport-Security` — but **not** `Content-Security-Policy`. |
| **Fix** | Add `Content-Security-Policy: default-src 'self'` to the middleware (value may need tuning for WebSocket/SSE endpoints). |

### C4 — No Token Refresh / Auto-Logout on Expiry (Frontend + Backend)

| Property | Value |
|----------|-------|
| **Files** | `auth/jwt.py`, `api/middleware.py`, `frontend/src/api/client.ts`, `frontend/src/components/auth/AuthGuard.tsx` |
| **Severity** | CRITICAL |
| **Risk** | When the JWT expires (24h), the frontend continues making requests that fail with 401. There is no interceptor to detect this, clear the token, and redirect to login. Users will see silent failures or broken UIs. |
| **Evidence** | JWT has a 24-hour expiry (`ACCESS_TOKEN_EXPIRE_MINUTES = 1440`). The frontend `apiFetch` has no response interceptor for 401s. No refresh token mechanism. `AuthGuard` and `AuthProvider` never validate token expiry. |
| **Fix** | Add a 401 response interceptor in `apiFetch` that clears token and redirects to `/login`. Add token expiry check in `AuthProvider`. Consider implementing refresh tokens with shorter access token TTL. |

### C5 — No CSRF Protection (Backend)

| Property | Value |
|----------|-------|
| **File** | `api/main.py`, `api/middleware.py` |
| **Severity** | CRITICAL |
| **Risk** | No CSRF tokens or SameSite cookie enforcement leaves the API vulnerable to cross-site request forgery if a user is logged in and visits a malicious site |
| **Evidence** | No CSRF middleware. No SameSite attribute on any cookies (though the app uses localStorage primarily). `allow_credentials=True` in CORS with `allow_origins` set to specific origins partially mitigates but is not a CSRF solution. |
| **Fix** | If cookies are ever used for auth, add CSRF tokens. For localStorage-based auth (current model), ensure CORS is strictly configured and consider adding `SameSite` headers if switching to httpOnly cookies. |

---

## HIGH Items

### H1 — No Frontend `.env` Files (Config Management)

| Property | Value |
|----------|-------|
| **File** | `frontend/` (no `.env`, `.env.development`, `.env.production`) |
| **Severity** | HIGH |
| **Risk** | Build-time environment configuration is opaque. Developers must modify `api/client.ts` or set OS env vars to change API URLs. No documented setup flow. |
| **Evidence** | Zero `.env*` files in `frontend/`. The `VITE_API_URL` defaults to `http://localhost:8000` and `VITE_WS_URL` defaults to `ws://localhost:8000` as hardcoded fallbacks in `api/client.ts:1` and `websocket/client.ts:9`. |
| **Fix** | Create `frontend/.env.development` (defaults for dev) and document `VITE_*` vars in the project README. CI builds should set these at build time. |

### H2 — No Build Optimization / Code Splitting (Frontend)

| Property | Value |
|----------|-------|
| **File** | `frontend/vite.config.ts`, `frontend/src/App.tsx` |
| **Severity** | HIGH |
| **Risk** | All 35+ page components are statically imported. The initial bundle includes the entire application. Large initial load time. |
| **Evidence** | `vite.config.ts` has no `build.rollupOptions.output.manualChunks`, no `build.chunkSizeWarningLimit`. `App.tsx` imports all 35+ pages statically. A `lazy-routes.ts` file exists with lazy loading for 4 pages but is not used in App.tsx. |
| **Fix** | Add manual chunks in vite.config.ts for `react`, `lightweight-charts`, `recharts`, `framer-motion`. Convert static imports in `App.tsx` to use `React.lazy()` (or the existing `lazyLoad` helper) for all route pages. |

### H3 — JWT in `localStorage` (Security)

| Property | Value |
|----------|-------|
| **File** | `frontend/src/api/client.ts:9`, `frontend/src/components/auth/AuthProvider.tsx` |
| **Severity** | HIGH |
| **Risk** | `localStorage` is accessible to any JavaScript executing in the same origin. A single XSS vulnerability exposes the JWT permanently. |
| **Evidence** | Token stored in `localStorage.getItem("auth_token")` / `setItem("auth_token")`. No `httpOnly` cookie option. No refresh token rotation. |
| **Fix** | Migrate to httpOnly cookies for the JWT (requires backend `Set-Cookie` header + cookie-based auth in middleware). Alternatively, accept the risk and mitigate with strong CSP and input sanitization. |

### H4 — WebSocket Token in URL Query Parameter (Security)

| Property | Value |
|----------|-------|
| **File** | `frontend/src/websocket/client.ts:21` |
| **Severity** | HIGH |
| **Risk** | The JWT is appended as `?token=<jwt>` in the WebSocket URL. This can be logged by proxies, load balancers, and server access logs — permanently exposing the token. |
| **Evidence** | `const url = \`${WS_BASE}${path}?token=${encodeURIComponent(token)}\` ;` (line 21). |
| **Fix** | Send the token as the first WebSocket message after connection, or use a dedicated `Sec-WebSocket-Protocol` header. |

### H5 — Database Session Leak Risk in Routes (Backend)

| Property | Value |
|----------|-------|
| **File** | Multiple route files in `api/routes/` |
| **Severity** | HIGH |
| **Risk** | Direct `session.close()` calls instead of the `session_scope()` context manager can leak database connections if an exception occurs before the close call. |
| **Evidence** | `database.py` provides `session_scope()` (line 229) but the codebase has 30+ instances of raw `get_session()` / `session.close()` patterns. The `session_scope()` context manager ensures proper commit/rollback/close in all paths. |
| **Fix** | Audit all route files and replace raw session patterns with `with session_scope() as session:` or use FastAPI dependency injection for session management. |

### H6 — Missing Error Monitoring / Sentry (Observability)

| Property | Value |
|----------|-------|
| **File** | Not present anywhere |
| **Severity** | HIGH |
| **Risk** | No production error tracking means unknown failures are invisible to the team |
| **Evidence** | No `sentry_sdk` or `opentelemetry-*` packages. Dockerfile.prod does not include Sentry. `PRODUCTION_READINESS.md` lists this as unchecked. `BACKLOG.md` item L-08 tracks this. |
| **Fix** | Add `sentry-sdk` to requirements.txt and initialize it in the `lifespan` handler. Configure DSN via `SENTRY_DSN` env var. |

### H7 — Vite Config Lacks `base` Path / Proxy / Build Settings (Frontend)

| Property | Value |
|----------|-------|
| **File** | `frontend/vite.config.ts` |
| **Severity** | HIGH |
| **Risk** | No `base` path means the app must be served from root. No dev proxy means CORS is required for development. No build output customization. |
| **Evidence** | `vite.config.ts` has only `plugins: [react(), tailwindcss()]`. No `base`, `build`, `server.proxy`, or `preview` configuration. |
| **Fix** | Add `base: '/'` explicitly, add `server.proxy` for API during development, and add `build.chunkSizeWarningLimit` and `build.rollupOptions.output.manualChunks`. |

### H8 — Redis Provisioned But Unused (Resource Waste)

| Property | Value |
|----------|-------|
| **Files** | `docker-compose.yml`, `docker-compose.prod.yml` (redis service), `requirements.txt` |
| **Severity** | HIGH |
| **Risk** | Redis is running in production with a password but no backend code connects to it. Unnecessary complexity and attack surface. |
| **Evidence** | Redis service defined in both compose files. `REDIS_URL` env var set in prod compose. Zero Python files import `redis`. The in-memory cache in `api/cache.py` does not use Redis. |
| **Fix** | Remove Redis from compose until a use case requires it, or integrate it for session caching / rate limiting and remove the in-memory cache. |

---

## MEDIUM Items

| ID | Finding | File(s) | Risk | Fix |
|----|---------|---------|------|-----|
| M1 | `lazy-routes.ts` dead code | `frontend/src/utils/lazy-routes.ts` | Unused exports; confusing dead code | Remove or wire into `App.tsx` |
| M2 | `scripts/` directory empty | `scripts/` | Backup cron job in compose will fail | Create `scripts/backup.sh` or remove compose reference |
| M3 | No `.dockerignore` | (Missing) | Unnecessary build context (node_modules, .venv, .git) | Create `.dockerignore` with Python + Node exclusions |
| M4 | `backups/` directory not created | (Missing), but in compose | Volume mount will fail | Create `backups/` directory or remove from compose |
| M5 | `LoginPage` bypasses `AuthProvider.login` | `LoginPage.tsx` | Duplicate auth path; inconsistent state | Use `useAuth().login()` instead of raw `apiFetch` |
| M6 | `startup()` not called in API lifespan | `api/main.py:74-90` | Startup validation runs only in CLI mode | Call `startup()` or at minimum `create_tables()` in lifespan |
| M7 | `CORS_ORIGINS` defaults to `*` for dev | `startup.py:33` | Overly permissive if env not set | Keep but ensure startup validator blocks `*` in production |
| M8 | `favicon.svg` referenced but not confirmed | `frontend/index.html:5` | Missing favicon on some deployments | Verify `public/favicon.svg` exists (it does) |
| M9 | No pre-commit hooks (lint/typecheck) | (Missing) | Inconsistent code quality | Add `husky` + `lint-staged` or similar |
| M10 | No `vite preview` config for testing built app | `vite.config.ts` | Served build may differ from dev | Add `preview` config matching production setup |
| M11 | `requirements.txt` has unpinned dependencies | `requirements.txt` | Non-reproducible builds | Pin exact versions with `pip freeze` |
| M12 | `healthcheck` in Dockerfile.arm64 missing trailing backslash | `Dockerfile.arm64:26-27` | `HEALTHCHECK CMD` and `ENTRYPOINT` on adjacent lines without continuation will cause build to fail | Add ` \` continuation to HEALTHCHECK or ensure both are separate instructions |

---

## LOW Items

| ID | Finding | File(s) | Fix |
|----|---------|---------|-----|
| L1 | `RiskEngine.score()` called with dummy data in periodic broadcast | `api/main.py:366` | Pass real market/risk data instead of `{"atr": 0}` |
| L2 | `HealthService.cache()` creates new `LiveMarketEngine()` each call | `monitoring/health.py:119-123` | Use singleton or dependency injection |
| L3 | No explicit `tsconfig.json` path aliases | `frontend/tsconfig.json` | Add `@/` alias for cleaner imports |
| L4 | No `favicon.svg` alternative formats | `frontend/index.html:5` | Add PNG fallback for older browsers |
| L5 | Duplicate `useAuth` export (context vs direct) | `AuthProvider.tsx:66`, `AuthGuard.tsx:16` | Remove duplicate, keep only `AuthProvider`'s context-based version |
| L6 | `API_ENV` not used anywhere in `app.py` | `app.py` | Engine doesn't distinguish dev/prod modes |

---

## Summary

| Severity | Count | Key Action |
|----------|-------|------------|
| **BLOCKER** | 3 | Wire QueryClientProvider, wire logging, add rate limiting |
| **CRITICAL** | 5 | Alembic migrations, monitoring config files, API CSP, token refresh, CSRF protection |
| **HIGH** | 8 | Frontend .env, code splitting, JWT storage security, WS token exposure, session leaks, Sentry, Vite config, Redis cleanup |
| **MEDIUM** | 12 | Various infrastructure and code quality gaps |
| **LOW** | 6 | Minor cleanup opportunities |

**Total: 34 findings**

### Deployment Order (Recommended)

1. **Fix BLOCKERs B1–B3** — Without these, the application cannot function reliably in production.
2. **Fix CRITICAL C2** (monitoring configs) — Prod docker-compose will fail to start.
3. **Fix CRITICAL C1, C4, C5** — Migrations, auth reliability, and CSRF protection.
4. **Fix HIGH H1–H8** — Config management, security hardening, build optimization.
5. **Address MEDIUM/LOW** items over subsequent sprint(s).

---

*This report was generated programmatically by auditing the codebase at `C:\elite-decision-engine`. Each finding was verified by examining the relevant source files, configuration, and Docker/deployment artifacts.*
