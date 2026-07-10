# DECISIONS — Elite Decision Engine

> Every strategic decision recorded with date, reason, and impact.

---

## Architecture Decisions

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| 2026-07-03 | Paper-first execution architecture | Validate trading logic before live trading risk | All execution is paper-only; live infrastructure dormant |
| 2026-07-03 | Python/FastAPI backend | Async support, type hints, modern ecosystem | Fast API development, good typing story |
| 2026-07-03 | React 19 + TypeScript frontend | Type safety, modern tooling, Vite speed | Strict mode enabled, zero TS errors |
| 2026-07-03 | PostgreSQL database | Production-grade, JSON support, reliability | SQLite fallback for dev/testing |
| 2026-07-03 | SQLAlchemy ORM | Declarative models, migration-ready, Pythonic | Models: Signal, Trade, User, Notification, Watchlist, JournalEntry |
| 2026-07-03 | Hyperliquid as primary exchange | Perpetual futures, low fees, good API | Binance as secondary connector |
| 2026-07-05 | 5-component weighted scoring (trend 30%, volume 20%, btc 20%, mtf 20%, risk 10%) | Balanced multi-factor signal evaluation | Scores must sum to 1.0, enforced in config.py |
| 2026-07-05 | Dependency Injection pattern | Testability, swappable components | All major components accept injectable deps |
| 2026-07-05 | Logging over print | Production-grade observability | Rotating file handlers: engine.log, trade.log, error.log |
| 2026-07-06 | Synchronous blocking main loop | Simplicity for single-developer project | DecisionEngine.run() is `while True`; async refactor planned for EPIC 2 |

## Security Decisions

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| 2026-07-10 | Default-deny auth middleware | Most routes should require authentication | Only /health, /auth/register, /auth/login are public |
| 2026-07-10 | JWT token on WebSocket connections | Prevent unauthorized real-time data access | Token passed as ?token= query param, validated on connect |
| 2026-07-10 | Security headers on all responses | OWASP best practice | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, etc. |
| 2026-07-10 | CORS restricted to configured origin | Prevent cross-origin abuse | Default: http://localhost:5173; production must set explicitly |
| 2026-07-10 | CSP in index.html | Prevent XSS via script injection | Restricts script/style sources, allows TradingView widgets |
| 2026-07-10 | Password validation (8-char minimum) | Basic security hygiene | Prevents trivially weak passwords |

## Release Decisions

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| 2026-07-10 | Closed Beta before Public Beta | Validate real-world behavior, gather UX feedback, identify scaling issues | 10-50 testers; polish items addressed before public |
| 2026-07-10 | Release Candidate approved | 953 backend tests pass, 60 frontend tests pass, all core features work | Platform demonstrably functional end-to-end |
| 2026-07-10 | Not production-ready yet | Security gaps (localStorage token, no rate limiting), missing ops files | 5-week hardening sprint needed for production |

## Frontend Decisions

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| 2026-07-10 | Zustand for client state | Lightweight, no boilerplate | 5 stores: UI, preferences, workspace, terminal |
| 2026-07-10 | React Query for server state | Caching, stale-while-revalidate | 10s staleTime, automatic refetch |
| 2026-07-10 | TradingView widget for charts | Industry-standard, lightweight | Avoids building custom charting engine |
| 2026-07-10 | Dark theme only | Trader preference, reduces design surface | CSS variables for theming |
| 2026-07-10 | Code-split routes with lazy loading | Performance optimization | All routes lazy-loaded via Suspense |

## Configuration Decisions

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| 2026-07-03 | Environment-based configuration | 12-factor app, production flexibility | config.py loads from .env with validation |
| 2026-07-03 | CHECK_INTERVAL = 10s default | Balance responsiveness vs API rate limits | Configurable via env var |
| 2026-07-03 | MIN_SCORE = 85 default | Only high-confidence signals traded | Prevents low-quality signal execution |
| 2026-07-03 | MAX_OPEN_TRADES = 3 default | Risk management — limit concurrent exposure | Configurable per deployment |

---

*Last updated: 2026-07-10*
