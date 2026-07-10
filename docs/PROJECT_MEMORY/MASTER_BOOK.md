# MASTER BOOK — Elite Decision Engine

> Single source of truth for the entire project. Every AI assistant starts here.

---

## 1. Project Vision

Elite Decision Engine transforms from a paper trading engine into an **Enterprise AI-powered Decision Intelligence Platform**. It evaluates market signals through a multi-stage decision pipeline, executes paper trades, monitors TP/SL, and provides real-time monitoring via a rich web dashboard — all powered by AI scoring, regime detection, and intelligence feeds.

**Target users**: Algorithmic traders, quant analysts, crypto portfolio managers.

---

## 2. Architecture

```
TradingSignal (DB: OPEN)
    ↓
ExecutionLoop.run_once()
    ↓
DecisionPipeline.evaluate()
    ├── MarketDataCollector.get_ohlcv()
    ├── BTCHealthFilter.evaluate()
    ├── ScoringEngine.score()          (5 components: trend, volume, btc, mtf, risk)
    └── ConfidenceEngine.calculate()
    ↓
RiskManager.evaluate_trade()
    ↓
PositionSizingEngine.calculate()      (ATR-based)
    ↓
TradeEngine.create_trade()            (TP/SL calcs → DB → Notifications)
    ↓
Trade (SQLAlchemy → PostgreSQL)
    ↓
PaperExecutor.monitor_open_trades()   (TP/SL check → Auto-close stale)
```

### Core Modules

| Module | Path | Responsibility |
|--------|------|----------------|
| **Core** | `core/` | DecisionEngine, ConfidenceEngine — main loop, decision logic |
| **Market Data** | `market_data/` | HyperliquidCollector, IndicatorEngine, VolumeEngine, BTCHealth, VolatilityEngine, MTFEngine, LiveEngine |
| **Exchange** | `exchange/` | ExchangeAdapter (ABC), HyperliquidConnector, BinanceConnector |
| **Execution** | `execution/` | ExecutionLoop, DecisionPipeline, TradeEngine, PaperExecutor, TPSLEngine |
| **Scoring** | `scoring/` | ScoringEngine, RegimeAI, SignalRankingAI, RiskEngine, PerformanceIntelligence, BacktestV2 |
| **API** | `api/` | FastAPI app, 31 REST routes, 6 WebSocket endpoints, auth middleware, security headers |
| **Frontend** | `frontend/` | React 19 + Vite 8, 33 pages, 200+ components, 5 Zustand stores, 31 routes |
| **Database** | `database.py` | SQLAlchemy models (Signal, Trade, User, UserSettings, Notification, Watchlist, JournalEntry) |
| **Services** | `services/` | ExplanationService, CoordinatorService, AnalyticsService, TerminalService |
| **Risk** | `risk_manager.py` | 5-rule risk evaluation (exposure, daily loss, position size, open trades, correlation) |
| **Portfolio** | `portfolio_engine.py` | 14 portfolio metrics (PnL, win rate, drawdown, etc.) |
| **Performance** | `performance_engine.py` | 12 performance metrics (Sharpe, Sortino, profit factor, etc.) |
| **Notifications** | `notifications/` | Event foundation, Dispatcher, WebSocket integration |
| **Scanner** | `scanner/` | Multi-timeframe scanner, opportunity categories |
| **Strategies** | `strategies/` | Trend, momentum, breakout, reversal, liquidity strategies |
| **Filters** | `filters/` | Signal filtering logic |
| **Auth** | `auth/` | JWT authentication |
| **Config** | `config.py` | Environment-based configuration with validation |
| **Logging** | `logging_config.py` | Rotating file handlers (engine.log, trade.log, error.log) |
| **Startup** | `startup.py` | Environment validation, DB connectivity check |

---

## 3. Completed Epics

| Epic | Name | Commit | Status |
|------|------|--------|--------|
| — | Foundation (DecisionEngine, Pipeline, PaperExecutor, Scoring) | Initial commits | ✅ DONE |
| — | Execution Loop v1 (orchestration, signal contract, TP/SL) | `c7f83fc` | ✅ DONE |
| — | Risk Engine, Position Sizing, Portfolio/Performance Analytics | `d5230ff`, `14d58f0` | ✅ DONE |
| — | Live Execution Routing, Hyperliquid Adapter | `99b3ba8` | ✅ DONE |
| — | Notification System (events, dispatcher, WebSocket) | `23d7738` | ✅ DONE |
| — | Frontend Dashboard (React, 33 pages, WebSocket) | `2da4b70` | ✅ DONE |
| — | Sprints 39-60 (Scanners, Backtest, Monitoring, Memory) | `5a79920`–`5bbd850` | ✅ DONE |
| Epic 1 | MIP Integration — pipeline, scoring, paper executor, guard, API | `8f214b2` | ✅ DONE |
| Epic 2 | Elite Scanner Core — trend, momentum, breakout, reversal, liquidity | `c6c4a2c` | ✅ DONE |
| Epic 3 | Market Intelligence — funding, OI, Fear & Greed, News, Whale, Exchange Flow | `191a1b4` | ✅ DONE |
| Epic 4 | Elite Scanner PRO — probability, risk, confidence, filters, watchlist | `36df0b2` | ✅ DONE |
| Epic 5 | Decision Intelligence — aggregator, confidence v2, timeline, explanation | `1be5eee` | ✅ DONE |
| Epic 6 | Elite Terminal Backend — unified API, terminal service, scanner websocket | `abd7e9b` | ✅ DONE |
| Epic 7 | Platform Optimization — pycache cleanup, gitignore, datetime fix, DB optimization | `6ebaa13` | ✅ DONE |
| Epic 8 | Beta Readiness — reports, fixes, full test pass | `1b61087` | ✅ DONE |
| — | Elite Terminal: Enterprise Decision Intelligence Platform | `1204952` | ✅ DONE |
| — | UX audit, UI polish, beta certification docs | `5e35d84` | ✅ DONE |
| — | Security hardening sprint | `7770f92` | ✅ DONE |
| — | Product Completion Sprint — Release Candidate | `818c4ee` | ✅ DONE |

---

## 4. Current Release

- **Version**: 1.0.0 Release Candidate
- **Branch**: `execution-layer`
- **Last Commit**: `818c4ee` — Product Completion Sprint — Release Candidate (2026-07-10)
- **Status**: Ready for Closed Beta

---

## 5. Current Phase

**Closed Beta Preparation** — The platform has completed all 8 Epics, security hardening, and UX polish. Release Decision: ✅ READY FOR CLOSED BETA. Outstanding items are polish/ops, not architectural flaws.

---

## 6. Development Rules

From `CLAUDE.md`:

- One feature = one commit
- Never modify unrelated files
- Preserve existing architecture
- Do not rewrite working components
- Always review git diff before commit
- Run relevant tests before commit
- Never commit failing code

**Coding Style**: Small commits, Dependency Injection, Logging (not print), Type hints, Preserve SQLAlchemy models, No duplicate logic.

**Before Every Commit**: `git diff` → compile → run tests → commit → push.

---

## 7. AI Architecture

### Backend (Python)
- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy (PostgreSQL / SQLite fallback)
- **Auth**: JWT (HS256)
- **Scoring**: 5-component weighted engine (trend 30%, volume 20%, btc 20%, mtf 20%, risk 10%)
- **Execution**: Synchronous blocking main loop (`DecisionEngine.run()` → `while True`)
- **Logging**: Rotating file handlers (10MB, 5 backups)

### Frontend (TypeScript)
- **Framework**: React 19 + Vite 8
- **State**: React Query (server state), Zustand (client state), React Context (auth/theme)
- **UI**: Custom design system, dark theme, 40+ widgets
- **Charts**: TradingView widget integration
- **WebSocket**: Client with exponential backoff reconnection
- **Build**: 530KB JS, 55KB CSS, 336ms build time

### Database
- **Engine**: PostgreSQL 16 (production), SQLite (development/testing)
- **Models**: Signal, Trade, User, UserSettings, Notification, Watchlist, JournalEntry
- **Migrations**: Not yet implemented (Alembic planned for EPIC 1)
- **Sessions**: `session_scope()` context manager, `get_session()` factory

### API
- **REST**: 31 route modules, ~100 endpoints
- **WebSocket**: 6 rooms (trade updates, market data, notifications, scanner, portfolio, dashboard)
- **Auth**: JWT middleware, default-deny approach (only health + auth endpoints are public)
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, HSTS

### Security
- JWT auth on all endpoints (default-deny)
- WebSocket token validation
- CORS restricted to configured origins
- CSP headers in index.html
- Security headers on all responses
- Password validation (8-char minimum)
- TypeScript strict mode enabled

---

## 8. Roadmap

### Completed
- Foundation (DecisionEngine, Pipeline, PaperExecutor)
- Execution Loop v1
- Risk Engine, Position Sizing, Analytics
- Live Execution Routing, Exchange Adapters
- Notification System, WebSocket
- Frontend Dashboard (33 pages)
- Sprints 39-60
- Epics 1-8 (Scanner, Market Intelligence, Decision Intelligence, Terminal, Optimization, Beta Readiness)
- Security Hardening, UX Polish

### Next (from ROADMAP.md)
- **EPIC 1**: Foundation Hardening (pin deps, pyproject.toml, Alembic, API versioning)
- **EPIC 2**: Execution Engine Optimization (async loop, caching, pagination)
- **EPIC 3**: Elite Scanner (multi-timeframe, divergence, pattern recognition)
- **EPIC 4**: Market Intelligence Platform (on-chain, correlation, liquidity heatmap)
- **EPIC 5**: News Intelligence (NLP sentiment, news ingestion)
- **EPIC 6**: Whale Intelligence (on-chain tracking, whale alerts)
- **EPIC 7**: Probability Engine (ML outcome prediction, Monte Carlo)
- **EPIC 8**: Elite Terminal (pro trading terminal, advanced charts)
- **EPIC 9**: Portfolio Intelligence (VaR, optimization, attribution)
- **EPIC 10**: AI Assistant (LLM integration, natural language, RAG)
- **EPIC 11**: Production Readiness (E2E tests, CI/CD, load testing)
- **EPIC 12**: Beta Launch (integration testing, security audit, onboarding)

---

## 9. Founder Decisions

1. **Paper-first architecture**: All execution is paper-only. Live trading infrastructure exists but is dormant.
2. **Single-developer project**: 116+ commits, solo development.
3. **Stack choice**: Python/FastAPI backend, React/TypeScript frontend, PostgreSQL database.
4. **Exchange focus**: Hyperliquid primary, Binance secondary.
5. **Security approach**: Default-deny auth, JWT tokens, security headers hardening.
6. **Release strategy**: Closed Beta before Public Beta — validate real-world behavior first.

---

## 10. CTO Principles

1. **Never commit failing code** — tests must pass before commit.
2. **Preserve architecture** — do not rewrite working components.
3. **Dependency Injection** — all major components accept injectable dependencies.
4. **Logging over print** — structured logging with rotating handlers.
5. **One feature = one commit** — atomic, reviewable changes.
6. **No duplicate logic** —DRY across the codebase.
7. **Small commits** — frequent, focused, reversible.
8. **Type hints everywhere** — Python + TypeScript strict mode.

---

## 11. Current Priorities

1. **Closed Beta launch** — validate with 10-50 testers
2. **Fix ConfidenceEngine math bug** (BP2) — double-scaling causes every signal approved
3. **Fix ATRr_14 typo** (BP3) — breaks indicator pipeline
4. **Add database migrations** (Alembic) — schema changes are dangerous without them
5. **Pin dependency versions** — reproducible builds
6. **Wire real data sources** into ExplanationService and CoordinatorService

---

## 12. Known Limitations

| Category | Limitation | Impact |
|----------|-----------|--------|
| Functional | No live exchange integration | Paper trading only |
| Functional | ConfidenceEngine math bug (double-scaling) | Every signal approved |
| Functional | ATRr_14 typo | All indicator data zero |
| Functional | Intelligence sources are stub/dummy data | No real market intelligence |
| Scalability | Portfolio engine loads all trades in memory | Memory pressure at 10k+ trades |
| Scalability | No pagination on list endpoints | Degraded UX with large datasets |
| Scalability | No rate limiting on API | Susceptible to abuse |
| Security | JWT secret key < 32 bytes | Cryptographic weakness warning |
| Security | No ForeignKey on Trade.signal_id | Orphaned trades possible |
| Maintainability | 32 datetime.utcnow() deprecation warnings | Python 3.14 breakage |
| Maintainability | 7 legacy test files with zero assertions | Confidence gap |
| Maintainability | Dead code artifacts (DC1-9) | Maintenance burden |

---

## 13. Future Vision

1. **Enterprise AI Platform** — AI-powered decision support with LLM assistant
2. **Multi-user SaaS** — role-based access, team workspaces, audit logging
3. **Live Trading** — exchange integration with circuit breakers and position reconciliation
4. **News & Whale Intelligence** — NLP sentiment, on-chain whale tracking
5. **Probability Engine** — ML outcome prediction, Monte Carlo simulation
6. **Strategy Marketplace** — shared strategies, community features
7. **White-label** — enterprise deployment with custom branding

---

*Last updated: 2026-07-10 | Branch: execution-layer | Commit: 818c4ee*
