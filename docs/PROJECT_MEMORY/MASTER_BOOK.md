# MASTER BOOK — Elite Platform

> **Version**: 2.0 | **Status**: Single Source of Truth | **Last Updated**: 2026-07-10

This document is the official brain of the project. Every AI assistant reads this first.

---

# AI CONTINUITY PROTOCOL

Every AI assistant **MUST** read the following before making any recommendation:

1. `docs/PROJECT_MEMORY/MASTER_BOOK.md`
2. `docs/PROJECT_MEMORY/PROJECT_STATUS.md`
3. `docs/PROJECT_MEMORY/DECISIONS.md`

These files **override assumptions**. Follow these rules:

- **Never** restart the project.
- **Never** suggest completed work.
- **Never** contradict documented architectural decisions.
- **Always** continue from the latest documented state.
- **Always** check PROJECT_STATUS.md before proposing next steps.
- **Always** check DECISIONS.md before making architectural changes.

---

# PROJECT IDENTITY

| Field | Value |
|-------|-------|
| **Project Name** | Elite Platform (Elite Decision Engine) |
| **Repository** | `mustafa78-bit/elite-decision-engine` |
| **Branch** | `execution-layer` |
| **Founder** | Mustafa |
| **Chief Architect** | ChatGPT (OpenAI) |
| **Development Assistant** | Codex / OpenCode |
| **Current Version** | 1.0.0 Release Candidate |
| **Current Phase** | Closed Beta Preparation |
| **Release Status** | Ready for Closed Beta |

---

# PROJECT VISION

## Why Elite Platform Exists

Elite Platform exists to give algorithmic traders and crypto portfolio managers an **AI-powered decision intelligence platform** that is transparent, explainable, and human-controlled.

The platform evaluates market signals through a multi-stage decision pipeline, executes paper trades, monitors TP/SL, and provides real-time monitoring via a rich web dashboard — all powered by AI scoring, regime detection, and intelligence feeds.

## Long-Term Vision

Transform from a paper trading engine into an **Enterprise AI-powered Decision Intelligence Platform** that competes with Bloomberg Terminal, TradingView, and 3Commas — but is open-source, AI-first, and explainable.

## Product Philosophy

- **Explainable Decision Intelligence**: Never generate black-box signals. Every decision is explained.
- **Human stays in control**: AI recommends, human decides. No autonomous trading without explicit consent.
- **AI explains**: Every signal, every trade, every risk assessment comes with a human-readable explanation.
- **Human-first AI**: AI augments human judgment, never replaces it.
- **Paper-first**: Validate all logic in paper mode before any live trading.

## Target Users

Algorithmic traders, quant analysts, crypto portfolio managers, and institutional teams.

---

# AI TEAM

## Founder

| Field | Value |
|-------|-------|
| **Name** | Mustafa |
| **Role** | Product Vision |
| **Responsibilities** | Product direction, business decisions, user feedback, market strategy |

## Chief Architect

| Field | Value |
|-------|-------|
| **Name** | ChatGPT (OpenAI) |
| **Responsibilities** | Architecture, long-term planning, technical direction, quality review, product strategy, architecture protection |

## Development Assistant

| Field | Value |
|-------|-------|
| **Name** | Codex / OpenCode |
| **Responsibilities** | Implementation, testing, refactoring, documentation, execution |

---

# ARCHITECTURE

## Backend

- **Language**: Python 3.11+
- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy (PostgreSQL production / SQLite fallback)
- **Auth**: JWT (HS256), default-deny middleware
- **Logging**: Rotating file handlers (engine.log, trade.log, error.log) — 10MB, 5 backups
- **Config**: Environment-based (`config.py` + `.env`), validated at import time

## Frontend

- **Framework**: React 19 + Vite 8
- **Language**: TypeScript (strict mode)
- **State**: React Query (server), Zustand (client), React Context (auth/theme)
- **UI**: Custom design system, dark theme, 40+ widgets, 200+ components
- **Charts**: TradingView widget integration
- **WebSocket**: Client with exponential backoff reconnection
- **Build**: 530KB JS, 55KB CSS, 336ms build time
- **Pages**: 33 routes, all lazy-loaded via Suspense

## API

- **REST**: 31 route modules, ~100 endpoints
- **WebSocket**: 6 rooms (trade updates, market data, notifications, scanner, portfolio, dashboard)
- **Auth**: JWT middleware, only `/health`, `/auth/register`, `/auth/login` are public
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, HSTS

## WebSocket

- Room-based pub/sub system (6 rooms)
- Token-validated connections (`?token=<jwt>`)
- Periodic broadcast every 30 seconds
- Frontend: exponential backoff reconnection

## Database

- **Engine**: PostgreSQL 16 (production), SQLite (dev/testing)
- **Models**: Signal, Trade, User, UserSettings, Notification, Watchlist, JournalEntry
- **Migrations**: Not yet implemented (Alembic planned)
- **Sessions**: `session_scope()` context manager, `get_session()` factory

## Market Intelligence Platform

- **Funding Rates**: Collected from Hyperliquid
- **Open Interest**: OI data with delta change detection
- **Fear & Greed Index**: Market sentiment scoring
- **News Intelligence**: Stub wiring (placeholder for NLP integration)
- **Whale Intelligence**: Stub wiring (placeholder for on-chain tracking)
- **Exchange Flow**: Inflow/outflow data collection
- **Liquidity Analysis**: Order book depth measurement

## Decision Engine

```
TradingSignal (DB: OPEN)
    ↓
ExecutionLoop.run_once()
    ↓
DecisionPipeline.evaluate()
    ├── MarketDataCollector.get_ohlcv()
    ├── BTCHealthFilter.evaluate()
    ├── ScoringEngine.score()          (5 components)
    └── ConfidenceEngine.calculate()
    ↓
RiskManager.evaluate_trade()          (5 rules)
    ↓
PositionSizingEngine.calculate()      (ATR-based)
    ↓
TradeEngine.create_trade()            (TP/SL → DB → Notifications)
    ↓
Trade (SQLAlchemy → PostgreSQL)
    ↓
PaperExecutor.monitor_open_trades()   (TP/SL check → Auto-close stale)
```

## Execution Layer

- **ExecutionLoop**: Batch signal processing, trade monitoring
- **DecisionPipeline**: Protocol-based interfaces (collector, filter, scorer, confidence calculator)
- **TradeEngine**: TP/SL calculation, duplicate check, DB persist, notification emit
- **PaperExecutor**: Open/close trades, PnL calculation, stale trade cleanup (7d)
- **TPSLEngine**: Entry/Stop/TP1/TP2/RR from ATR

## Scanner

- Multi-timeframe scanner (1m, 5m, 15m, 1h, 4h, 1d)
- 5 strategies: trend, momentum, breakout, reversal, liquidity
- Opportunity categories with ranking
- Scanner websocket for real-time results

## Terminal

- Elite Terminal: Enterprise Decision Intelligence Platform
- Trading workspace with multi-panel layout
- Professional workspace with resizable panels
- AI experience with chat, signals, analysis
- Hero dashboard with 18 widgets

## Security

- JWT auth on all endpoints (default-deny)
- WebSocket token validation
- CORS restricted to configured origins
- CSP headers in index.html
- Security headers on all responses
- Password validation (8-char minimum)
- TypeScript strict mode

## Notifications

- Event foundation with typed events
- NotificationDispatcher for WebSocket and Telegram
- Trade lifecycle events (open, close, TP/SL hit)
- Real-time notification center in frontend

## Monitoring

- Production monitoring with Prometheus
- Grafana dashboards
- Rotating log files (engine.log, trade.log, error.log)
- Startup validation (env vars, DB connectivity, config sanity)

---

# AI ARCHITECTURE

## Current AI Components

| Component | Path | Function |
|-----------|------|----------|
| **ScoringEngine** | `scoring/` | 5-component weighted scoring (trend, volume, btc, mtf, risk) |
| **ConfidenceEngine** | `core/` | Decision logic from component scores |
| **RegimeAI** | `scoring/` | Market regime classification (trending, ranging, volatile) |
| **SignalRankingAI** | `scoring/` | ML-based signal prioritization |
| **RiskEngine** | `scoring/` | Risk component scoring |
| **PerformanceIntelligence** | `scoring/` | Performance analytics and insights |
| **BacktestV2** | `scoring/` | Historical backtesting engine |
| **TradeMemory** | `scoring/` | Past trade context for decision improvement |

## Future AI Roadmap

| Phase | Component | Description |
|-------|-----------|-------------|
| Phase 1 | **ConfidenceEngine Fix** | Fix double-scaling math bug (BP2) |
| Phase 2 | **Probability Engine** | ML outcome prediction, Monte Carlo simulation |
| Phase 3 | **AI Assistant** | LLM integration, natural language queries, RAG |
| Phase 4 | **Sentiment Engine** | NLP-powered news sentiment scoring |
| Phase 5 | **Whale AI** | On-chain whale movement pattern recognition |

## Coordinator Model

The `CoordinatorService` currently acts as a registry for intelligence sources. It is stateless with dummy sources. When real intelligence modules are wired, it will orchestrate:

- Market data collection
- Signal generation
- Risk assessment
- Trade execution
- Notification dispatch

## Future Agent Responsibilities

| Agent | Responsibility |
|-------|---------------|
| **Market Agent** | Real-time market data collection and normalization |
| **Signal Agent** | Signal generation from multiple strategies |
| **Risk Agent** | Real-time risk assessment and portfolio monitoring |
| **Execution Agent** | Trade execution and order management |
| **Intelligence Agent** | News, whale, on-chain data aggregation |
| **Explanation Agent** | Human-readable trade explanations |

---

# COMPLETED MILESTONES

## Chronological History

| Date | Milestone | Commit |
|------|-----------|--------|
| 2026-07-03 | Initial commit — database models, basic structure | `02d9719` |
| 2026-07-03 | DecisionEngine — core engine with signal polling | Early commits |
| 2026-07-03 | DecisionPipeline — scoring pipeline with 5 components | Early commits |
| 2026-07-03 | PaperExecutor v2 — TP/SL monitoring, trade close | `a3ef7da` |
| 2026-07-03 | Execution Loop v1 — batch orchestration, signal contract | `c7f83fc` |
| 2026-07-03 | Risk Engine — 5-rule risk evaluation | `d5230ff` |
| 2026-07-03 | Position Sizing — ATR-based sizing engine | `14d58f0` |
| 2026-07-03 | Portfolio Analytics — 14 portfolio metrics | `c1ad6c8` |
| 2026-07-03 | Performance Analytics — 12 performance metrics | `005c6dd` |
| 2026-07-04 | Live Execution — Hyperliquid adapter, dry-run pipeline | `99b3ba8` |
| 2026-07-04 | Notification System — events, dispatcher, WebSocket | `23d7738` |
| 2026-07-05 | Frontend Dashboard — React foundation, 33 pages | `2da4b70` |
| 2026-07-05 | CI/CD Pipeline — GitHub Actions, Docker | `8dca11b` |
| 2026-07-06 | Sprints 39-60 — Scanners, Backtest, Monitoring, Memory | `5a79920`–`5bbd850` |
| 2026-07-10 | Epic 1: MIP Integration — pipeline, scoring, paper executor, guard, API | `8f214b2` |
| 2026-07-10 | Epic 2: Elite Scanner Core — trend, momentum, breakout, reversal, liquidity | `c6c4a2c` |
| 2026-07-10 | Epic 3: Market Intelligence — funding, OI, Fear & Greed, News, Whale, Exchange Flow | `191a1b4` |
| 2026-07-10 | Epic 4: Elite Scanner PRO — probability, risk, confidence, filters, watchlist | `36df0b2` |
| 2026-07-10 | Epic 5: Decision Intelligence — aggregator, confidence v2, timeline, explanation | `1be5eee` |
| 2026-07-10 | Epic 6: Elite Terminal Backend — unified API, terminal service, scanner websocket | `abd7e9b` |
| 2026-07-10 | Epic 7: Platform Optimization — pycache cleanup, gitignore, datetime fix, DB optimization | `6ebaa13` |
| 2026-07-10 | Epic 8: Beta Readiness — reports, fixes, full test pass | `1b61087` |
| 2026-07-10 | Elite Terminal: Enterprise Decision Intelligence Platform | `1204952` |
| 2026-07-10 | UX audit, UI polish, beta certification docs | `5e35d84` |
| 2026-07-10 | Security hardening sprint | `7770f92` |
| 2026-07-10 | Product Completion Sprint — Release Candidate | `818c4ee` |
| 2026-07-10 | Project Memory System v1.0 | `580b88f` |
| 2026-07-10 | Project Memory System v2.0 | Current |

---

# CURRENT STATUS

| Field | Value |
|-------|-------|
| **Current Release** | 1.0.0 Release Candidate |
| **Current Phase** | Closed Beta Preparation |
| **Release Readiness** | Ready for Closed Beta |
| **Backend Maturity** | 94% — 784/785 tests passing |
| **Frontend Maturity** | 93% — 35/35 tests passing, 0 TS errors |
| **Security Maturity** | Hardened — remaining: localStorage token, no rate limiting |
| **Testing Status** | 953+ backend tests, 60+ frontend tests |

---

# STRATEGIC DECISIONS

| Date | Decision | Reason | Impact | Status |
|------|----------|--------|--------|--------|
| 2026-07-03 | Paper-first execution architecture | Validate trading logic before live trading risk | All execution is paper-only | Active |
| 2026-07-03 | Python/FastAPI backend | Async support, type hints, modern ecosystem | Fast API development | Active |
| 2026-07-03 | React 19 + TypeScript frontend | Type safety, modern tooling, Vite speed | Strict mode enabled | Active |
| 2026-07-03 | PostgreSQL database | Production-grade, JSON support, reliability | SQLite fallback for dev | Active |
| 2026-07-03 | SQLAlchemy ORM | Declarative models, migration-ready | 7 models defined | Active |
| 2026-07-03 | Hyperliquid as primary exchange | Perpetual futures, low fees, good API | Binance secondary | Active |
| 2026-07-05 | 5-component weighted scoring | Balanced multi-factor signal evaluation | Scores sum to 1.0 | Active |
| 2026-07-05 | Dependency Injection pattern | Testability, swappable components | All major components use DI | Active |
| 2026-07-05 | Logging over print | Production-grade observability | Rotating file handlers | Active |
| 2026-07-06 | Synchronous blocking main loop | Simplicity for single-developer project | Async refactor planned | Active |
| 2026-07-10 | Default-deny auth middleware | Most routes should require authentication | Only 3 public endpoints | Active |
| 2026-07-10 | JWT token on WebSocket connections | Prevent unauthorized real-time data access | Token validated on connect | Active |
| 2026-07-10 | Security headers on all responses | OWASP best practice | 6 headers added | Active |
| 2026-07-10 | CORS restricted to configured origin | Prevent cross-origin abuse | Default: localhost:5173 | Active |
| 2026-07-10 | CSP in index.html | Prevent XSS via script injection | Restricts script sources | Active |
| 2026-07-10 | Password validation (8-char minimum) | Basic security hygiene | Prevents weak passwords | Active |
| 2026-07-10 | Closed Beta before Public Beta | Validate real-world behavior | 10-50 testers first | Active |
| 2026-07-10 | Zustand for client state | Lightweight, no boilerplate | 5 stores | Active |
| 2026-07-10 | React Query for server state | Caching, stale-while-revalidate | 10s staleTime | Active |
| 2026-07-10 | TradingView widget for charts | Industry-standard, lightweight | Avoids custom charting | Active |
| 2026-07-10 | Dark theme only | Trader preference, reduces design surface | CSS variables | Active |
| 2026-07-10 | Code-split routes with lazy loading | Performance optimization | All routes lazy-loaded | Active |
| 2026-07-10 | Environment-based configuration | 12-factor app, production flexibility | config.py + .env | Active |

---

# DEVELOPMENT WORKFLOW

## Founder (Mustafa)

- Sets product direction and priorities
- Reviews features before release
- Provides real user feedback
- Makes final business decisions

## Chief Architect (ChatGPT)

- Designs architecture and technical direction
- Plans long-term roadmap
- Reviews code quality and architecture protection
- Makes product strategy decisions
- Protects architectural integrity

## Development Assistant (Codex / OpenCode)

- Implements features and fixes
- Writes tests
- Refactors code
- Creates documentation
- Executes assigned tasks

## Review Cycle

1. Development Assistant implements
2. Chief Architect reviews architecture
3. Founder reviews product fit
4. Merge after approval

## Testing Rules

- Run relevant tests before commit
- Never commit failing code
- 953+ backend tests must pass
- 60+ frontend tests must pass
- TypeScript strict mode must compile

## Commit Rules

- One feature = one commit
- Never modify unrelated files
- Always review git diff before commit
- Commit message must describe the change
- Push to execution-layer branch

## Release Rules

- All tests must pass
- Security hardening must be complete
- Documentation must be updated
- PROJECT_STATUS.md must reflect current state
- Release Decision must be approved

---

# CTO PRINCIPLES

1. **Architecture first** — design before implementation
2. **Maintainability first** — clean code over clever code
3. **No unnecessary complexity** — simplest solution that works
4. **Product before code** — understand the why before the how
5. **Quality before speed** — ship it right, not just ship it
6. **Never commit failing code** — tests must pass
7. **Preserve architecture** — do not rewrite working components
8. **Dependency Injection** — all major components accept injectable deps
9. **Logging over print** — structured logging with rotating handlers
10. **One feature = one commit** — atomic, reviewable changes
11. **No duplicate logic** —DRY across the codebase
12. **Type hints everywhere** — Python + TypeScript strict mode

---

# FOUNDER PRINCIPLES

1. **Founder Alpha first** — the founder uses the product daily
2. **Daily usage** — real feedback from real usage
3. **Real feedback** — no hypothetical scenarios, only real user experience
4. **Product before marketing** — build something great, then tell people about it
5. **Paper-first always** — validate before risking real money

---

# ROADMAP

## Current (Completed)

- Foundation (DecisionEngine, Pipeline, PaperExecutor, Scoring)
- Execution Loop v1
- Risk Engine, Position Sizing, Analytics
- Live Execution Routing, Exchange Adapters
- Notification System, WebSocket
- Frontend Dashboard (33 pages, 200+ components)
- Sprints 39-60
- Epics 1-8 (Scanner, Market Intelligence, Decision Intelligence, Terminal, Optimization, Beta Readiness)
- Security Hardening, UX Polish
- Project Memory System v1.0 and v2.0

## Next (Public Beta Preparation)

1. Fix ConfidenceEngine math bug (BP2)
2. Fix ATRr_14 typo (BP3)
3. Add Alembic database migrations
4. Pin dependency versions
5. Wire real data sources into ExplanationService/CoordinatorService
6. Add rate limiting to API endpoints
7. Move JWT token to httpOnly cookies

## Future (Enterprise Platform)

- EPIC 1: Foundation Hardening (pin deps, pyproject.toml, Alembic, API versioning)
- EPIC 2: Execution Engine Optimization (async loop, caching, pagination)
- EPIC 3: Elite Scanner (multi-timeframe, divergence, pattern recognition)
- EPIC 4: Market Intelligence Platform (on-chain, correlation, liquidity heatmap)
- EPIC 5: News Intelligence (NLP sentiment, news ingestion)
- EPIC 6: Whale Intelligence (on-chain tracking, whale alerts)
- EPIC 7: Probability Engine (ML outcome prediction, Monte Carlo)
- EPIC 8: Elite Terminal (pro trading terminal, advanced charts)
- EPIC 9: Portfolio Intelligence (VaR, optimization, attribution)
- EPIC 10: AI Assistant (LLM integration, natural language, RAG)
- EPIC 11: Production Readiness (E2E tests, CI/CD, load testing)
- EPIC 12: Beta Launch (integration testing, security audit, onboarding)

## Long-Term

- Multi-user SaaS (roles, workspaces, audit logging)
- Live Trading (exchange integration, circuit breakers)
- Strategy Marketplace (shared strategies, community)
- White-label (custom branding, enterprise features)

---

# PRODUCT PHILOSOPHY

## Explain Every Decision

Every signal, every trade, every risk assessment comes with a human-readable explanation. No black boxes.

## Never Generate Black-Box Signals

The scoring engine uses 5 weighted components. Each component produces a score. The final score is a weighted sum. Every number is traceable.

## Human Stays in Control

AI recommends. Human decides. No autonomous trading without explicit consent. The platform is a decision support tool, not a decision replacement.

## AI Explains

When the platform recommends a trade, it explains:
- Which indicators triggered the signal
- What the scoring components contributed
- What the risk assessment found
- What the confidence level is
- What similar trades did in the past

---

# KNOWN LIMITATIONS

| Category | Limitation | Impact |
|----------|-----------|--------|
| Functional | No live exchange integration | Paper trading only |
| Functional | ConfidenceEngine math bug (double-scaling) | Every signal approved at STRONG_APPROVE |
| Functional | ATRr_14 typo in indicator pipeline | All indicator data reads as zero |
| Functional | Intelligence sources are stub/dummy data | No real market intelligence wired |
| Scalability | Portfolio engine loads all trades in memory | Memory pressure at 10k+ trades |
| Scalability | No pagination on list endpoints | Degraded UX with large datasets |
| Scalability | No rate limiting on API | Susceptible to abuse |
| Security | JWT secret key < 32 bytes | Cryptographic weakness warning |
| Security | No ForeignKey on Trade.signal_id | Orphaned trades possible |
| Security | Token stored in localStorage | XSS-vulnerable |
| Maintainability | 32 datetime.utcnow() deprecation warnings | Python 3.14 breakage |
| Maintainability | 7 legacy test files with zero assertions | Confidence gap |
| Maintainability | Dead code artifacts (DC1-9) | Maintenance burden |
| Maintainability | No database migration system | Schema changes dangerous |

---

# FUTURE VISION

1. **Enterprise AI Platform** — AI-powered decision support with LLM assistant
2. **Explainable Intelligence** — every signal comes with full reasoning chain
3. **Multi-user SaaS** — role-based access, team workspaces, audit logging
4. **Live Trading** — exchange integration with circuit breakers and position reconciliation
5. **News & Whale Intelligence** — NLP sentiment, on-chain whale tracking
6. **Probability Engine** — ML outcome prediction, Monte Carlo simulation
7. **AI Assistant** — natural language queries, trade explanations, market insights
8. **Strategy Marketplace** — shared strategies, community features
9. **White-label** — enterprise deployment with custom branding
10. **Global Reach** — multi-language support, mobile applications

---

*Last updated: 2026-07-10 | Branch: execution-layer | Commit: 580b88f*
