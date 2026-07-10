# ATLAS REPORT — Elite Decision Engine

> **Classification**: Confidential — Chief Architect Analysis
> **Date**: July 2026
> **Author**: Mustafa, Chief Software Architect
> **Version**: 1.0.0 (Pre-Beta)

---

## Table of Contents

1. [Repository Overview](#1-repository-overview)
2. [Backend Architecture](#2-backend-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [API Layer](#4-api-layer)
5. [Database Layer](#5-database-layer)
6. [WebSocket Layer](#6-websocket-layer)
7. [Exchange Integration](#7-exchange-integration)
8. [Test Coverage](#8-test-coverage)
9. [Infrastructure & DevOps](#9-infrastructure--devops)
10. [Git Analysis](#10-git-analysis)
11. [Strengths](#11-strengths)
12. [Weaknesses](#12-weaknesses)
13. [Technical Debt](#13-technical-debt)
14. [Duplicate Logic](#14-duplicate-logic)
15. [Dead Code](#15-dead-code)
16. [Bottlenecks](#16-bottlenecks)
17. [Scalability Risks](#17-scalability-risks)
18. [Security Audit](#18-security-audit)

---

## 1. Repository Overview

| Metric | Value |
|--------|-------|
| **Total Commits** | 116 |
| **Contributors** | 2 (Mustafa: 109, mustafa78-bit: 7) |
| **Branches** | 4 (`main`, `execution-layer`, `origin/live-execution`) |
| **Python Files** | ~100+ |
| **TypeScript/TSX Files** | ~200+ |
| **Test Files (Python)** | ~60 |
| **Test Files (Frontend)** | ~20 |
| **Docker Files** | 5 |
| **CI/CD** | 1 GitHub Workflow |
| **Total LOC (Est.)** | ~30,000+ |

### Directory Tree (Top-Level)

```
elite-decision-engine/
├── api/                    # FastAPI REST + WebSocket
├── auth/                   # JWT authentication
├── core/                   # Decision engine, confidence engine
├── deploy/                 # Nginx config
├── dto/                    # Data transfer objects
├── exchange/               # Exchange adapter layer (Hyperliquid, Binance)
├── execution/              # Pipeline, loop, paper executor, trade engine, TP/SL
├── features/               # Feature store
├── filters/                # BTC health filter
├── frontend/               # React/TypeScript SPA
├── market/                 # Domain models, providers, indicators, cache
├── market_data/            # Collectors, live engine, normalizer, volatility
├── memory/                 # Trade memory
├── monitoring/             # Health service
├── notifications/          # Event dispatcher, serializer
├── orders/                 # Order management
├── risk/                   # Risk models, execution guard
├── scoring/                # Scoring, regime AI, risk engine, ranking
├── services/               # Service layer (analytics, portfolio, KPI, etc.)
├── shadow/                 # Shadow trading engine
├── simulator/              # Execution simulator
├── strategies/             # Strategy engine, registry, scoring
├── tests/                  # Backend test suite
├── utils/                  # Utility modules
├── .github/workflows/      # CI/CD
├── app.py                  # Application entry point
├── config.py               # Configuration
├── database.py             # SQLAlchemy models + session
├── logging_config.py       # Structured logging
├── startup.py              # Startup validation
├── portfolio_engine.py     # Portfolio analytics
├── performance_engine.py   # Performance metrics
├── position_sizing.py      # Position sizing
├── risk_manager.py         # Risk manager
├── docker-compose.yml      # Dev compose
├── docker-compose.prod.yml # Production compose (9 services)
├── Dockerfile              # Multi-stage build
├── Dockerfile.prod         # Production build
├── Dockerfile.arm64        # ARM64 build
└── requirements.txt        # Python dependencies (no version pins)
```

---

## 2. Backend Architecture

### Core Architecture Pattern

The backend follows a **layered pipeline architecture** with dependency injection:

```
TradingSignal
    ↓
DecisionPipeline (MarketData → Filters → Scoring → Confidence)
    ↓
ExecutionLoop (Ranking → Pipeline → Risk → Sizing → Trade)
    ↓
TradeEngine (TP/SL → DB persistence → Notifications)
    ↓
Trade (SQLAlchemy Model)
    ↓
PaperExecutor (Monitoring → PnL → TP/SL verification → Close)
```

### Module Breakdown

#### Core Layer (`core/`)
- **DecisionEngine** (`engine.py`): Main loop polling for open signals, delegating to ExecutionLoop. Implements a blocking `while True` loop with `time.sleep(CHECK_INTERVAL)`.
- **ConfidenceEngine** (`confidence_engine.py`): Decision logic from scoring data.

#### Execution Layer (`execution/`)
- **ExecutionLoop** (`execution_loop.py`): Orchestrator that processes signal batches, applies SignalRankingAI, calls DecisionPipeline, RiskManager, PositionSizingEngine, and TradeEngine.
- **DecisionPipeline** (`pipeline.py`): Coordinates market data collection → filters → scoring engine → confidence engine. Uses protocols for DI.
- **TradeEngine** (`trade_engine.py`): Creates Trade records in DB with TP/SL levels calculated by TPSLEngine. Emits TradeEvent notifications.
- **PaperExecutor** (`paper_executor.py`): Manages paper trade lifecycle: open, monitor (TP/SL check), close, stale trade handling (7 days). Emits TRADE_CLOSED events.
- **TPSLEngine** (`tp_sl.py`): Calculates entry/stop/tp1/tp2/rr from ATR and side.

#### Scoring Layer (`scoring/`)
- **ScoringEngine** (`scoring_engine.py`): Weighted scoring from 5 components (trend 30%, volume 20%, BTC 20%, MTF 20%, risk 10%).
- **RegimeAI** (`regime_ai.py`): Market regime classifier (TREND, DOWNTREND, RECOVERY, RANGE, DEAD) with trend strength, volatility class, and market phase.
- **RegimeEngine** (`regime_engine.py`): Alternative regime detection.
- **RiskEngine** (`risk_engine.py`): Risk scoring component.
- **SignalRankingAI** (`signal_ranking_ai.py`): ML-based signal ranking.
- **PerformanceIntelligence** (`performance_intelligence.py`): Performance analysis.
- **BacktestV2** (`backtest_v2.py`): Historical backtesting engine.

#### Data Layer (`market_data/`)
- **HyperliquidCollector** (`collector.py`): OHLCV data collection.
- **IndicatorEngine** (`indicators.py`): Technical indicators (EMA20/50/200, RSI, ATR).
- **VolumeEngine** (`volume.py`): Volume analysis and scoring.
- **BTCHealth** (`btc_health.py`): BTC market health scoring.
- **VolatilityEngine** (`volatility.py`): Volatility measurement.
- **MTFEngine** (`mtf.py`): Multi-timeframe analysis.
- **LiveEngine** (`live/engine.py`): Real-time market data engine.

#### Exchange Layer (`exchange/`)
- **ExchangeAdapter** (`base.py`): Abstract base with 10 abstract methods.
- **HyperliquidConnector** (`hyperliquid/connector.py`): Hyperliquid exchange implementation.
- **BinanceConnector** (`binance/connector.py`): Binance exchange implementation.
- **Models**: Candle, Order, Position, Balance, Ticker.
- **Exceptions**: Custom exchange error hierarchy.

#### Risk Layer (`risk/`)
- **RiskModels** (`models.py`): Risk data structures.
- **ExecutionGuard** (`execution_guard.py`): Execution safety checks.

#### Service Layer (`services/`)
- 9 service modules: analytics, coordinator, explanation, KPI, notification, portfolio, preferences, timeline, watchlist, widget.

---

## 3. Frontend Architecture

### Stack

| Technology | Version |
|-----------|---------|
| React | 19.2.7 |
| TypeScript | 6.0.2 |
| Vite | 8.1.1 |
| Vitest | 4.1.10 |
| TanStack Query | 5.101.2 |
| Zustand | 5.0.14 |
| Tailwind CSS | 4.3.2 |
| Framer Motion | 12.42.2 |
| React Router | 7.18.1 |

### State Management Architecture

```
┌──────────────────────────────────────────────────┐
│                  App.tsx                          │
│  ┌──────────┐ ┌──────────┐ ┌───────────────┐    │
│  │ Zustand  │ │ React    │ │ React Query   │    │
│  │ Stores   │ │ Context  │ │ (Server State)│    │
│  │ (5)      │ │ (Auth,   │ │               │    │
│  │          │ │  Theme)  │ │               │    │
│  └──────────┘ └──────────┘ └───────────────┘    │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ WebSocket (6 rooms) → OutletContext → Pages  │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### Component Inventory

| Category | Count | Description |
|----------|-------|-------------|
| **UI Primitives** | 19 | Button, Card, Badge, Table, Dialog, Tabs, Tooltip, etc. |
| **Layout** | 15 | Shell, Sidebar, Topbar, Header, ErrorBoundary, ToastProvider |
| **Dashboard Widgets** | 30+ | KPI cards, PnL chart, portfolio summary, risk metrics, etc. |
| **Trading** | 22 | ChartPanel, OrderPanel, OrderBook, PositionTracker, SymbolSearch |
| **Signals** | 6 | SignalTable, SignalTimeline, ScoreBreakdown, ConfidenceBadge |
| **Workspace** | 8 | MultiPanelLayout, ResizablePanel, DockableWidget |
| **System** | 11 | ThemeCustomizer, OnboardingWizard, KeyboardShortcuts, AuditLog |
| **Pages** | 33 | Dashboard, Trades, Market, Portfolio, Risk, Signals, etc. |

### API Client

17 API modules with ~50 endpoint functions. Base URL hardcoded to `http://localhost:8000`.

### WebSocket Client

6 connection functions (trades, analytics, dashboard, portfolio, notifications, preferences) to `ws://localhost:8000`. Auto-reconnect with up to 10 retries.

---

## 4. API Layer

### REST API

**Framework**: FastAPI with 31 route modules.

| Route Module | Prefix | Endpoints |
|-------------|--------|-----------|
| `auth` | `/auth` | register, login, refresh |
| `signals` | `/signals` | CRUD |
| `signals_ranking` | `/signals/ranking` | ranking |
| `execution` | `/execution` | status |
| `trading_control` | `/trading-control` | control |
| `market` | `/market` | market data |
| `market_live` | `/market/live` | live market |
| `portfolio` | `/portfolio` | portfolio |
| `portfolio_detail` | `/portfolio` | detail |
| `risk` | `/risk` | risk metrics |
| `regime` | `/regime` | regime |
| `analytics` | `/analytics` | analytics |
| `kpi` | `/kpi` | KPIs |
| `dashboard` | `/dashboard` | dashboard |
| `widgets` | `/widgets` | widgets |
| `notifications` | `/notifications` | notifications |
| `paper_trading` | `/paper-trading` | paper trading |
| `performance` | `/performance` | performance |
| `backtest` | `/backtest` | backtest |
| `journal` | `/journal` | trade journal |
| `intelligence` | `/intelligence` | intelligence |
| `explanation` | `/explanation` | explanations |
| `coordination` | `/coordination` | coordination |
| `monitoring` | `/monitoring` | monitoring |
| `preferences` | `/preferences` | preferences |
| `watchlists` | `/watchlists` | watchlists |
| `timeline` | `/timeline` | timeline |
| `users` | `/users` | users |
| **Total** | **31 routers** | **~60+ endpoints** |

### WebSocket Endpoints

| Endpoint | Purpose | Broadcast Interval |
|----------|---------|-------------------|
| `/ws/trades` | Trade events | Event-driven + 30s |
| `/ws/analytics` | Analytics data | 30s |
| `/ws/dashboard` | Dashboard data | 30s |
| `/ws/portfolio` | Portfolio data | 30s |
| `/ws/notifications` | Notification events | Event-driven + 30s |
| `/ws/preferences` | Preference sync | 30s |

---

## 5. Database Layer

### SQLAlchemy Models (7 tables)

| Table | Key Fields | Relationships |
|-------|-----------|--------------|
| **signals** | id, symbol, side, timeframe, score, confidence, status | Referenced by trades.signal_id |
| **trades** | id, signal_id, symbol, side, entry, stop, tp1, tp2, rr, pnl, status | References signals |
| **users** | id, username, email, hashed_password | Referenced by user_settings |
| **user_settings** | id, user_id, timezone, dashboard_config, risk_preferences, theme | References users |
| **notifications** | id, user_id, event_type, payload, read | References users |
| **watchlists** | id, user_id, name, symbols | References users |
| **journal_entries** | id, symbol, side, entry_price, exit_price, score, confidence, result, pnl | Optional signal_id, trade_id |

### Database Configuration

- **Default**: PostgreSQL 16 via `DATABASE_URL` or individual `POSTGRES_*` vars.
- **Test**: SQLite (`test_elite.db`).
- **Pool**: `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`.
- **Migrations**: None — tables created via `Base.metadata.create_all()`.

---

## 6. WebSocket Layer

### Backend (`api/websocket/manager.py`)

- **WebSocketManager**: Room-based pub/sub.
- **6 rooms**: trades, analytics, dashboard, portfolio, notifications, preferences.
- **Periodic broadcast**: Every 30 seconds via `_periodic_broadcast()`.
- **Broadcast payloads**: MarketEvent (price, regime, BTC health, volatility), PriceUpdateEvent, CandleUpdateEvent, VolumeUpdateEvent, RiskEvent.

### Frontend (`frontend/src/websocket/client.ts`)

- 5 connection functions (trades already connected in App.tsx).
- Auto-reconnect with 10 retries at 3s intervals.
- **App.tsx**: Consolidates all WS state into `outletContext` passed via Layout.

---

## 7. Exchange Integration

### Current State

| Exchange | Status | Capabilities |
|----------|--------|-------------|
| **Hyperliquid** | ✅ Connected | Read-only OHLCV data, ticker, positions, account balance |
| **Binance** | ✅ Connected | Read-only via connector interface |
| **Adapter Layer** | ✅ Complete | Abstract ExchangeAdapter with 10 methods |

### Live Trading Status

- **Shadow Trading** (`shadow/shadow_engine.py`): Implemented.
- **Execution Simulator** (`simulator/execution_simulator.py`): Implemented.
- **Order Management** (`orders/order_manager.py`): Implemented.
- **Execution Guard** (`risk/execution_guard.py`): Implemented.
- **Live Execution** (real money): **NOT YET — paper trading only.**

---

## 8. Test Coverage

### Backend Tests (~60 test files)

| Test Category | File Count | Coverage Areas |
|--------------|-----------|----------------|
| **Execution** | 8 | Pipeline, trade engine, paper executor, TP/SL, execution simulator |
| **Scoring** | 8 | Scoring engine, risk engine, regime AI, signal ranking, backtest, performance |
| **Market Data** | 8 | Indicators, collector, volatility, volume, MTF, BTC, funding, OI |
| **API Routes** | 12 | Auth, analytics, coordinator, dashboard, execution, explanation, new routes |
| **Exchange** | 4 | Base, Binance, Hyperliquid adapters, models |
| **Infrastructure** | 8 | Auth, notification dispatcher/serializer, WebSocket manager, order manager |
| **Integration** | 4 | End-to-end, edge cases, batch operations |
| **Other** | 8+ | Portfolio, performance, position sizing, risk manager, BTC, feature store |

### Frontend Tests (20 test files)

| Test Category | File Count | Coverage Areas |
|--------------|-----------|----------------|
| **Components** | 17 | UI components, accessibility, AI widgets, theme, workspace, etc. |
| **API** | 2 | Client, widgets test |
| **Pages** | 1 | 404 page |

---

## 9. Infrastructure & DevOps

### Docker

| File | Purpose |
|------|---------|
| `Dockerfile` | Dev multi-stage (Node → Python) |
| `Dockerfile.prod` | Production 3-stage with non-root user, healthcheck, 4 workers |
| `Dockerfile.arm64` | ARM64 variant of prod |
| `docker-compose.yml` | Dev: DB (Postgres 16) + Redis 7 + API |
| `docker-compose.prod.yml` | Prod: 9 services (Traefik v3, Postgres, Redis, API, Nginx, Prometheus, Grafana, Backup) |

### Production Architecture (docker-compose.prod.yml)

```
Traefik v3 (TLS via Let's Encrypt)
├── api.elite-decision.io → API (4 workers, 1000 concurrency)
├── app.elite-decision.io → Nginx (SPA)
└── monitor.elite-decision.io → Grafana

Services:
├── PostgreSQL 16 (persistent volume)
├── Redis 7 (password auth)
├── Prometheus (30d retention)
├── Grafana (auto-provisioned)
└── Backup (cron → S3 via pg_dump + aws-cli)
```

### CI/CD (`.github/workflows/ci.yml`)

- **Backend**: Python 3.12, ruff lint, pytest (Postgres service container).
- **Frontend**: Node 22, npm ci, tsc + vite build.
- **Triggers**: Push to `main`/`execution-layer`, PR to `main`.
- **Missing**: No Docker build/push, no deployment, no integration test step.

### Monitoring

- **Health Service** (`monitoring/health.py`): DB health, collector health, cache health, execution health, dependency health, config health, error tracking.
- **Health endpoint**: `/health` returns status, service name, env, uptime.
- **Grafana + Prometheus** configured in prod compose.

---

## 10. Git Analysis

### Branch Strategy

```
main ────────────────────────────────────────────────
  \                                                    \
   execution-layer ── Sprint 39 ─→ ... ─→ Sprint 60 ─→ HEAD
    \
     live-execution (stale)
```

### Commit Velocity

- **116 total commits**.
- **Latest 22 commits = Sprints 39–60** (22 sprints).
- Average: ~2 commits per sprint.
- Single primary author (Mustafa).

### Sprint History (Sprints 39–60)

| Sprint | Theme |
|--------|-------|
| 39 | Market Regime Engine |
| 40 | Signal Quality Engine |
| 41 | Trade Journal |
| 42 | Backtest Foundation |
| 43 | Final Live Terminal Polish |
| 44–46 | Exchange Adapters (Hyperliquid, Binance) |
| 47 | Market Data Normalization |
| 48 | Order Management |
| 49 | Execution Risk Guard |
| 50 | Shadow Live Trading |
| 51 | Execution Simulator |
| 52 | Strategy Engine V2 |
| 53 | Trading Control Center |
| 54 | Feature Store |
| 55 | Market Regime AI |
| 56 | Signal Ranking AI |
| 57 | Trade Memory |
| 58 | Performance Intelligence |
| 59 | Backtest Engine V2 |
| 60 | Production Monitoring & Observability |
| Latest | Market Intelligence + Risk Architecture |

---

## 11. Strengths

1. **Clean layered architecture**: Clear separation between pipeline, execution, and paper trading. Dependency injection makes testing feasible.
2. **Comprehensive test suite**: ~60 backend test files covering most modules.
3. **Production-grade Docker**: Multi-stage builds, non-root user, healthchecks, Traefik reverse proxy with auto-TLS.
4. **Rich frontend**: 30+ pages, 200+ components, custom design system, WebSocket integration.
5. **Structured logging**: Rotating file handlers, JSON output in production, module-level filtering.
6. **Exchange abstraction**: Clean adapter pattern supporting multiple exchanges.
7. **WebSocket architecture**: Room-based pub/sub with periodic broadcast and event-driven updates.
8. **Dark theme design system**: Consistent CSS custom properties, glass morphism, accessibility considerations.
9. **Startup validation**: Comprehensive startup checks (env vars, DB connectivity, table accessibility).
10. **Scoring modularity**: Weighted multi-component scoring system that can be tuned independently.

---

## 12. Weaknesses

1. **No version pins in `requirements.txt`**: All Python deps unpinned — builds are non-reproducible and subject to breakage.
2. **No `pyproject.toml` or `setup.py`**: No project metadata, no editable installs, no dependency grouping (dev vs prod).
3. **No `.dockerignore`**: Docker builds include `.git/`, `.venv/`, `node_modules/`, `__pycache__/` — slow builds, cache invalidation.
4. **Hardcoded API URLs in frontend**: `http://localhost:8000` hardcoded in `client.ts`. No environment variable configuration.
5. **No database migrations**: `create_all()` is non-idiomatic and dangerous for production schema evolution.
6. **Blocking main loop**: `DecisionEngine.run()` uses `time.sleep()` — blocks the main thread, not async-friendly.
7. **Missing backup script**: `docker-compose.prod.yml` references `/scripts/backup.sh` but file does not exist.
8. **No API versioning**: All endpoints are unversioned (`/signals`, not `/v1/signals`).
9. **Frontend test coverage is thin**: 20 test files vs 200+ components — mostly smoke tests.
10. **Mixed JS/TS patterns**: Duplicate WebSocket hooks, duplicate toast systems, inconsistent patterns.

---

## 13. Technical Debt

| Item | Severity | Impact | Effort to Fix |
|------|----------|--------|--------------|
| Unpinned Python deps | HIGH | Build reproducibility | Small |
| No DB migrations | HIGH | Schema evolution risk | Medium |
| Hardcoded frontend URLs | HIGH | Configuration management | Small |
| Blocking `while True` loop | MEDIUM | Scalability, responsiveness | Medium |
| Missing `pyproject.toml` | MEDIUM | Project metadata, install | Small |
| Missing `.dockerignore` | MEDIUM | Build efficiency | Small |
| Missing backup script | MEDIUM | Production backup | Small |
| Duplicate WebSocket hooks | LOW | Maintainability | Small |
| Duplicate toast systems | LOW | Maintainability | Small |
| No API versioning | LOW | API evolution | Medium |
| Mixed auth patterns (context vs localStorage) | LOW | Consistency | Small |
| Empty `scripts/` and `docs/` dirs | LOW | Project hygiene | Small |
| `config.py` with hardcoded trading params | LOW | Configuration flexibility | Small |

---

## 14. Duplicate Logic

1. **WebSocket hooks**: `hooks/useWebSocket.ts` and `lib/websocket-hooks.ts` both implement WebSocket connection management with different APIs.
2. **Toast notifications**: `hooks/useToast.ts` and `components/layout/ToastProvider.tsx` implement separate toast systems.
3. **Layout systems**: `Layout.tsx` (simpler) and `Shell.tsx` (advanced) both provide layout wrappers with different APIs.
4. **Auth guards**: `AuthProvider` (context-based) and `AuthGuard` (localStorage-only) implement authentication checks differently.
5. **Market data fetch**: Both `DecisionPipeline._fetch_market_data()` and `ScoringEngine.score()` call `collector.get_ohlcv()` independently — two separate network calls for the same data in a single pipeline run.
6. **`_is_empty_market_data()`**: Defined in both `DecisionPipeline` (pipeline.py:259) and `PaperExecutor` (paper_executor.py:505) as static methods.
7. **`_normalize_symbol()` / `_normalize_side()`**: String normalization scattered across multiple modules.

---

## 15. Dead Code

1. **Whale Page** (`WhalePage.tsx`): Placeholder with "Coming in Batch 5" — no backend integration.
2. **Liquidity Page** (`LiquidityPage.tsx`): Placeholder with "Coming in Batch 5" — no backend integration.
3. **Funding Page** (`FundingPage.tsx`): Renders UI but no backend data integration confirmed.
4. **OpenInterest Page** (`OpenInterestPage.tsx`): Renders UI but no backend data integration confirmed.
5. **`engine.log`, `trade.log`, `error.log`** in root and `tests/logs/`: Committed log files should be gitignored.
6. **`test_elite.db`** in root and `frontend/`: Committed test databases.
7. **`frontend/README.md`**: Generic Vite scaffold README — no project-specific content.
8. **Several API routes with `/health` endpoint**: Only `api/main.py` exposes `/health` but some route files may have duplicate health endpoints (check needed).
9. **`execution/paper_executor.py` `execute()` method**: Labeled "backward-compatible entry point" — may be unused.

---

## 16. Bottlenecks

1. **DecisionEngine.run()**: Single-threaded blocking loop. Cannot process signals concurrently. Each iteration blocks for `CHECK_INTERVAL` (10s).
2. **Double OHLCV fetch per pipeline run**: `DecisionPipeline.evaluate()` and `ScoringEngine.score()` both fetch the same OHLCV data separately.
3. **Synchronous WebSocket manager**: `manager.broadcast()` likely blocks on slow clients.
4. **No caching for market data**: Every scoring cycle fetches fresh OHLCV from Hyperliquid without any caching layer.
5. **Sequential signal processing**: `ExecutionLoop.run_once()` processes signals one-by-one. With 50+ signals, latency is linear.
6. **Session-per-operation**: Database sessions are opened and closed for every single query — no request-scoped sessions.
7. **30-second WebSocket broadcast interval**: Slow for real-time trading — 30s delay between market state updates.

---

## 17. Scalability Risks

1. **No async signal processing**: The blocking main loop cannot scale beyond one engine instance.
2. **Single-process uvicorn in dev**: Dev Dockerfile runs 1 worker — no horizontal scaling.
3. **No message queue**: No Redis pub/sub or RabbitMQ — WebSocket broadcasts are in-process only.
4. **No caching layer for API**: API routes query DB directly every request — no Redis caching.
5. **No rate limiting**: API endpoints have no rate limiting — vulnerable to abuse.
6. **No pagination for list endpoints**: `/signals`, `/trades`, `/notifications` return all rows without pagination.
7. **No read replicas**: PostgreSQL handles both reads and writes — no read scaling.
8. **Static frontend**: No SSR, no code splitting beyond 4 lazy routes, no PWA capabilities.

---

## 18. Security Audit

| Category | Finding | Severity |
|----------|---------|----------|
| **JWT** | JWT_SECRET default `change-me-in-production` in docker-compose.yml | HIGH |
| **CORS** | CORS allows `*` when origins contain `*` | MEDIUM |
| **Password** | Default Postgres password `postgres` in dev | MEDIUM |
| **API Keys** | HL_API_KEY/HL_SECRET in env file | MEDIUM |
| **Rate Limiting** | No rate limiting on any endpoint | MEDIUM |
| **SQL Injection** | SQLAlchemy ORM used — parameters are bound | LOW |
| **Dependency** | No Dependabot or automated vulnerability scanning | MEDIUM |
| **Secrets** | `.env` in gitignore — good. But secrets in compose files | MEDIUM |
| **TLS** | Traefik handles TLS in prod — secure | GOOD |
| **Auth Bypass** | `/health`, `/auth/*`, `/docs`, `/openapi.json` are public | ACCEPTABLE |
| **Non-root user** | Production Docker runs as `app` user | GOOD |
| **CSP** | Strict CSP in nginx.conf | GOOD |

---

*End of ATLAS REPORT*
