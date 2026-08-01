# Frontend Deployment Report — Vercel

**Date:** 2026-07-11  
**Phase:** Founder Alpha | **Release:** 0.96 RC  
**Platform:** Vercel (Serverless SPA)  
**Branch:** `execution-layer`

---

## Deployment Checklist

### 1. Production Build — ✅ PASS

| Check | Result |
|-------|--------|
| `tsc -b` (TypeScript) | 0 errors |
| `vite build` | Passed (624ms) |
| Exit code | 0 |

**Build output:** `frontend/dist/`

### 2. Vite Configuration — ⚠️ PASS (Minimal)

| Setting | Value | Verdict |
|---------|-------|---------|
| `base` | `/` (default) | ✅ Correct for Vercel |
| `build.outDir` | `dist` (default) | ✅ Vercel auto-detects |
| `server.proxy` | Not set | ⚠️ No dev proxy; API calls use absolute URLs |
| `build.rollupOptions` | Not set | ⚠️ No code splitting configured |
| `build.chunkSizeWarningLimit` | Not set | ⚠️ Default 500KB (exceeded) |
| `build.sourcemap` | Not set (default: false) | ✅ No source maps in production |

**Issue:** No `build.rollupOptions.output.manualChunks` — all vendor code (React, charts, motion, etc.) is bundled into a single JS file.

### 3. React Routing — ❌ NEEDS CONFIG

| Check | Status | Detail |
|-------|--------|--------|
| `BrowserRouter` | ✅ Present in `App.tsx` | Correct for SPA |
| SPA fallback | ❌ No `vercel.json` | Direct URL access to `/dashboard`, `/scanner`, etc. will return 404 on Vercel |

**Required:** Create `frontend/vercel.json` with rewrite rules:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

This is the **single blocking item** for Vercel deployment.

### 4. Environment Variables — ⚠️ NEEDS CONFIG

| Variable | Default | Required In Vercel Dashboard |
|----------|---------|------------------------------|
| `VITE_API_URL` | `http://localhost:8000` | ✅ Yes — set to production API URL |
| `VITE_WS_URL` | `ws://localhost:8000` | ✅ Yes — set to production WebSocket URL |

**Note:** No `.env` files exist in `frontend/`. Defaults are hardcoded in `src/api/client.ts:1` and `src/websocket/client.ts:9`. Without setting these in Vercel dashboard, the built app will call `localhost:8000`.

### 5. API Base URL — ⚠️ Hardcoded Fallback

| File | Line | Default |
|------|------|---------|
| `src/api/client.ts` | 1 | `http://localhost:8000` |
| `src/websocket/client.ts` | 9 | `ws://localhost:8000` |

The fallback uses `import.meta.env.VITE_API_URL ?? "http://localhost:8000"`. Must be overridden via Vercel environment variables.

### 6. Assets — ✅ PASS

| Asset | Source | In `dist/` |
|-------|--------|------------|
| `favicon.svg` | `frontend/public/favicon.svg` | ✅ |
| `icons.svg` | `frontend/public/icons.svg` | ✅ |
| Static files | `public/` | ✅ Copied to dist root |

### 7. Production Bundle — ⚠️ Single Chunk

| Asset | Size | Gzip |
|-------|------|------|
| `index-NQ8EnHRm.js` | **836 KB** | 230 KB |
| `index-BdAtloKx.css` | **64 KB** | 10 KB |

**Issue:** Single monolithic JS bundle exceeds 500KB warning threshold. No code splitting applied. All 35+ pages, 200+ components, and all vendor libraries (React, Recharts, Lightweight Charts, Framer Motion, etc.) are in one file.

**Recommendation:** Add `build.rollupOptions.output.manualChunks` to separate vendor chunks:
- `react-vendor` (React, React Router, React Query, React Hook Form)
- `charts` (Lightweight Charts, Recharts)
- `animation` (Framer Motion)
- `ui` (UI components)
- `pages` (route components via dynamic imports)

### 8. Source Maps — ✅ PASS

| Check | Result |
|-------|--------|
| `.map` files in dist | ❌ None found |
| Source code exposed | ✅ No source maps means no source code leak |

Vite 8 defaults to `sourcemap: false` in production builds.

### 9. Lazy Loading — ❌ NOT IMPLEMENTED

| Check | Status | Detail |
|-------|--------|--------|
| `React.lazy()` used | ❌ No | All 35+ pages statically imported in `App.tsx` |
| `lazyLoad` helper exists | ✅ Yes | `src/components/performance/lazy-load.tsx` |
| `lazy-routes.ts` exists | ✅ Yes | 4 lazy wrappers defined but **unused** |
| Docs claim | 💬 MASTER_BOOK.md line 415: "All routes lazy-loaded via Suspense" | ❌ Incorrect — static imports used |

**Impact:** Despite documentation claiming lazy loading is implemented, all route components are eagerly imported. This contributes to the large initial bundle (836KB JS).

**Recommendation:** Convert static imports in `App.tsx` to use `React.lazy()` + the existing `lazyLoad` helper. This would reduce initial load to ~200-300KB and load remaining pages on demand.

---

## Deployment Steps

### Prerequisites
1. Create a Vercel account and install Vercel CLI: `npm i -g vercel`
2. Set `VITE_API_URL` and `VITE_WS_URL` in Vercel dashboard (or `.env.production`)

### Required Files
Create `frontend/vercel.json`:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### Vercel Configuration

| Setting | Value |
|---------|-------|
| **Framework** | Vite |
| **Build command** | `npm run build` |
| **Output directory** | `dist` |
| **Root directory** | `frontend` (if deploying monorepo) |
| **Node version** | 22.x (from `package.json`) |

### Environment Variables (Vercel Dashboard)

| Name | Value | Example |
|------|-------|---------|
| `VITE_API_URL` | Production API URL | `https://api.elite-decision.io` |
| `VITE_WS_URL` | Production WebSocket URL | `wss://api.elite-decision.io` |

---

## Summary

| Category | Status | Blocking? |
|----------|--------|-----------|
| Production build | ✅ PASS | No |
| Vite configuration | ⚠️ Minimal | No |
| React routing | ❌ No `vercel.json` | **YES** |
| Environment variables | ⚠️ Needs config | Yes (without API URL) |
| API base URL | ⚠️ Hardcoded fallback | Yes (without env vars) |
| Assets | ✅ PASS | No |
| Production bundle | ⚠️ Single 836KB chunk | No |
| Source maps | ✅ Disabled | No |
| Lazy loading | ❌ Not implemented | No (performance only) |

### Blocking Items
1. **Create `frontend/vercel.json`** with SPA rewrite rules
2. **Set `VITE_API_URL` and `VITE_WS_URL`** in Vercel dashboard

### Recommended (Non-blocking)
3. Add `build.rollupOptions.output.manualChunks` for code splitting
4. Convert static route imports to `React.lazy()` to reduce initial bundle

---

*Report generated by auditing `C:\elite-decision-engine\frontend` against Vercel deployment requirements.*
