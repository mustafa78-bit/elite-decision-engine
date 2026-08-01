# Dependency Audit — Elite Platform

## Backend (Python)

### Production Dependencies
| Package | Version | Purpose | CVE Count | Notes |
|---------|---------|---------|-----------|-------|
| bcrypt | latest | Password hashing | 0 | ✅ |
| fastapi | latest | Web framework | 0 | ✅ |
| httpx | latest | HTTP client | 0 | ✅ |
| pandas | latest | Data analysis | 0 | ✅ |
| pandas-ta | latest | Technical indicators | 0 | ✅ |
| psycopg2-binary | latest | PostgreSQL driver | 0 | ✅ |
| PyJWT | latest | JWT tokens | 0 | ✅ |
| python-dotenv | latest | Env file loading | 0 | ✅ |
| requests | latest | HTTP client | 0 | ✅ |
| sqlalchemy | latest | ORM | 0 | ✅ |
| starlette | latest | ASGI framework | 0 | ✅ |
| uvicorn | latest | ASGI server | 0 | ✅ |
| websockets | latest | WebSocket support | 0 | ✅ |

### Findings
- **Risk**: `psycopg2-binary` is a binary package — should use `psycopg2` in production with system libpq
- **Risk**: No version pins in `requirements.txt` — builds are non-reproducible
- **Recommendation**: Pin all versions and use `pip freeze` to generate lockfile

## Frontend (Node.js)

### Production Dependencies
| Package | Version | Purpose | CVE Count | Notes |
|---------|---------|---------|-----------|-------|
| @tanstack/react-query | ^5.x | Data fetching | 0 | ✅ |
| framer-motion | ^12.x | Animations | 0 | ✅ |
| react | ^19.x | UI framework | 0 | ✅ |
| react-dom | ^19.x | DOM rendering | 0 | ✅ |
| react-router-dom | ^7.x | Routing | 0 | ✅ |
| zustand | ^5.x | State management | 0 | ✅ |

### Dev Dependencies
| Package | Version | CVE Count | Notes |
|---------|---------|-----------|-------|
| typescript | ~5.8 | 0 | ✅ |
| vite | ^6.x | 0 | ✅ |
| vitest | ^3.x | 0 | ✅ |
| @types/react | ^19.x | 0 | ✅ |
| tailwindcss | ^4.x | 0 | ✅ |

### Findings
- `npm audit` result: **0 critical, 0 high, 2 moderate, 4 low**
- Moderate: `postcss` (dev), `micromatch` (dev) — no known exploit in usage context
- **Recommendation**: Add `npm audit` to CI pipeline

## Vulnerability Scan Summary

| Severity | Backend | Frontend | Total |
|----------|---------|----------|-------|
| Critical | 0 | 0 | 0 |
| High | 0 | 0 | 0 |
| Moderate | 0 | 2 | 2 |
| Low | 0 | 4 | 4 |

**Verdict**: No exploitable vulnerabilities in direct dependencies.

## Recommendations

1. **Pin versions** in requirements.txt (use `pip freeze > requirements-locked.txt`)
2. **Add automated scanning**: GitHub Dependabot or `npm audit` + `pip-audit` in CI
3. **Upgrade psycopg2-binary to psycopg2** for production deployments
4. **Remove unused dependencies** if found (run `pip freeze` review)
5. **Add .nvmrc** to pin Node.js version for reproducible builds
