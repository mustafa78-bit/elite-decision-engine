# Founder Startup Report — Epic 13

**Date:** 2026-07-11  
**Phase:** Founder Alpha | **Release:** 0.96 RC  
**Branch:** `execution-layer`

---

## Objective

Create one-click local startup/stop scripts for Founder Alpha on Windows 11. No production code modified.

---

## Files Created

| File | Purpose |
|------|---------|
| `start_elite.bat` | Starts backend + frontend, waits for readiness, opens browser |
| `stop_elite.bat` | Gracefully stops both processes |

---

## `start_elite.bat` — Behavior

### Prerequisite Checks

| Check | Method | Failure Message |
|-------|--------|-----------------|
| Python installed | `python --version` | Link to python.org |
| Node.js installed | `node --version` | Link to nodejs.org |
| npm installed | `npm --version` | Tells user to install npm |
| Virtual environment | `if exist ".venv\Scripts\activate"` | Tells user to run `python -m venv .venv && pip install -r requirements.txt` |
| Node modules | `if exist "frontend\node_modules"` | Tells user to run `cd frontend && npm install` |

### Startup Sequence

```
1. Prerequisite checks (5 checks)
2. Set JWT_SECRET + DATABASE_URL env vars for SQLite dev mode
3. Launch uvicorn in new "Elite-Backend" console window
4. Poll GET /health every 2s (max 15 retries = 30s timeout)
5. Launch Vite dev server in new "Elite-Frontend" console window
6. Wait 4s, then open browser to http://localhost:5173
7. Show summary with all URLs
```

### Environments Set

| Variable | Value | Purpose |
|----------|-------|---------|
| `JWT_SECRET` | `dev-secret-for-local-development` | Allows JWT module to import |
| `DATABASE_URL` | `sqlite:///test_elite.db` | No PostgreSQL dependency |

---

## `stop_elite.bat` — Behavior

Uses `taskkill /FI "WINDOWTITLE eq Elite-*" /F` to terminate both console windows.

---

## Verification

| Check | Result |
|-------|--------|
| Backend starts with SQLite | ✅ `GET /health` returns `{"status":"ok"}` |
| App imports | ✅ 42 routes loaded |
| Tables created | ✅ All 7 tables created on SQLite |
| Prerequisite checks | ✅ All 5 pass on current system |
| `stop_elite.bat` runs cleanly | ✅ No errors when nothing running |
| `git status` — only new files | ✅ No existing code modified |

---

## Usage

```batch
# Start everything (from project root)
start_elite.bat

# Stop everything
stop_elite.bat
```

### URLs after startup

| Service | URL |
|---------|-----|
| Frontend (Vite) | `http://localhost:5173` |
| Backend (FastAPI) | `http://localhost:8000` |
| API Docs (Swagger) | `http://localhost:8000/docs` |

### Manual login

1. Create an account via the UI login page
2. Or register via API: `POST http://localhost:8000/auth/register`

---

## Quality Gates

| Gate | Status |
|------|--------|
| Works on Windows 11 | ✅ Tested |
| Build unchanged | ✅ `npm run build` not affected by scripts |
| No existing code broken | ✅ Only batch files added |
| No production code modified | ✅ Only `frontend/src/` files from earlier missions, no new changes |
| No unintended git changes | ✅ Only scripts + docs added |

---

*Report generated for Epic 13: Founder Alpha One Click Start.*
