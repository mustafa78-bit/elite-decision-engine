# ARCHITECTURE — Elite Decision Engine

> **Version**: 1.0.0 | **Status**: Pre-Beta | **Last Updated**: July 2026

---

## 1. System Overview

Elite Decision Engine is an AI-powered paper trading platform that evaluates market signals through a multi-stage decision pipeline, executes paper trades, and provides real-time monitoring via a rich web dashboard.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ELITE DECISION ENGINE                        │
│                                                                     │
│  ┌─────────┐   ┌──────────┐   ┌────────────┐   ┌────────────┐    │
│  │ Signals │──▶│Pipeline  │──▶│ Execution  │──▶│ Trade      │    │
│  │ (DB)    │   │(Scoring) │   │ Loop       │   │ Engine     │    │
│  └─────────┘   └──────────┘   └────────────┘   └─────┬──────┘    │
│                                                       │            │
│                                                       ▼            │
│                                              ┌────────────┐       │
│                                              │ Paper      │       │
│                                              │ Executor   │       │
│                                              │ (TP/SL)    │       │
│                                              └────────────┘       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Supporting Modules                         │  │
│  │  ┌────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────┐  │  │
│  │  │Market  │ │Scoring   │ │Risk    │ │Exchange  │ │Notif.│  │  │
│  │  │Data    │ │Engines   │ │Mgmt    │ │Adapters  │ │System │  │  │
│  │  └────────┘ └──────────┘ └────────┘ └──────────┘ └──────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    API Layer (FastAPI)                        │  │
│  │  ┌────────┐ ┌──────────┐ ┌────────┐ ┌──────────────────┐   │  │
│  │  │REST API│ │WebSocket │ │Auth    │ │Health & Monitoring│  │  │
│  │  │31 Rts  │ │6 Rooms   │ │JWT     │ │                  │   │  │
│  │  └────────┘ └──────────┘ └────────┘ └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Frontend (React 19 + Vite 8)                     │  │
│  │  33 Pages │ 200+ Components │ 5 Zustand Stores │ 31 Routes  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architectural Principles

1. **Layered Pipeline**: Each stage in the pipeline has a single responsibility. Pipeline → Loop → Engine → Executor.
2. **Dependency Injection**: All major components accept injectable dependencies for testability.
3. **Protocol-based Interfaces**: `DecisionPipeline` uses `Protocol` classes for collector, filter, scorer, and confidence calculator.
4. **Event-Driven Notifications**: Trade lifecycle events flow through `NotificationDispatcher` to WebSocket and Telegram.
5. **Separation of Concerns**: Market data, scoring, execution, risk, and notifications are isolated modules.
6. **Paper-First**: All execution is paper-only. Live trading infrastructure exists but is dormant.

---

## 3. Core Data Flow

### Trading Signal Flow

```
                 ┌─────────────────────┐
                 │    Database Poll    │
                 │  (DecisionEngine)   │
                 └─────────┬───────────┘
                           │ Open signals
                           ▼
                 ┌─────────────────────┐
                 │   ExecutionLoop    │
                 │  .run_once()       │
                 └─────────┬───────────┘
                           │ Signal list
                           ▼
                 ┌─────────────────────┐
                 │  SignalRankingAI    │  (optional ML ranking)
                 └─────────┬───────────┘
                           │ Ranked signals
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │Decision    │ │Decision    │ │Decision    │
     │Pipeline    │ │Pipeline    │ │Pipeline    │
     └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
           │              │              │
           │ 1. Fetch market data        │
           │ 2. Apply BTC filter         │
           │ 3. Score (5 components)     │
           │ 4. Confidence calculation   │
           ▼              ▼              ▼
     ┌──────────────────────────────────────┐
     │      TradeCandidate (or None)        │
     └──────────────┬───────────────────────┘
                    │ Approved candidate
                    ▼
     ┌──────────────────────────────────────┐
     │         RiskManager                  │
     │   evaluate_trade(candidate)          │
     └──────────────┬───────────────────────┘
                    │ RiskDecision (allowed/rejected)
                    ▼
     ┌──────────────────────────────────────┐
     │      PositionSizingEngine            │
     │   calculate(candidate)               │
     └──────────────┬───────────────────────┘
                    │ PositionSize (qty, notional, risk)
                    ▼
     ┌──────────────────────────────────────┐
     │          TradeEngine                 │
     │   create_trade(signal, entry, atr)   │
     │   1. TP/SL calculation               │
     │   2. Duplicate check                 │
     │   3. DB persist                      │
     │   4. Notification emit               │
     └──────────────┬───────────────────────┘
                    │ Trade record (DB)
                    ▼
     ┌──────────────────────────────────────┐
     │         PaperExecutor                │
     │   monitor_open_trades()              │
     │   1. Fetch current price             │
     │   2. Check TP/SL                     │
     │   3. Close if hit                    │
     │   4. Stale trade cleanup (7d)        │
     │   5. Notification emit               │
     └──────────────────────────────────────┘
```

### Data Flow Per Pipeline Run

```
Signal
  │
  ├── MarketDataCollector.get_ohlcv()     ◄── Hyperliquid API
  │
  ├── BTCHealthFilter.evaluate()          ◄── Market health check
  │
  ├── ScoringEngine.score()
  │     ├── IndicatorEngine.calculate()   ◄── EMA20/50/200, RSI, ATR
  │     ├── VolumeEngine.score()          ◄── Volume analysis
  │     ├── BTCHealth.score()             ◄── BTC health score
  │     ├── VolatilityEngine.score()      ◄── Volatility measurement
  │     ├── MTFEngine.score()             ◄── Multi-timeframe
  │     ├── RiskEngine.score()            ◄── Risk assessment
  │     └── Weighted aggregation          ◄── 5-component weighted score
  │
  ├── ConfidenceEngine.calculate()        ◄── Decision (APPROVE/REJECT)
  │
  ├── RegimeAI.detect()                   ◄── Market regime context
  │
  └── TradeMemory.list()                  ◄── Past trade context
```

---

## 4. Module Architecture

### 4.1 Core (`core/`)

```
DecisionEngine
├── run()             — Infinite loop polling signals every CHECK_INTERVAL
├── get_open_signals()— DB query for OPEN signals
└── process_signal()  — Delegates to ExecutionLoop.run_once()

ConfidenceEngine
└── calculate()       — Decision logic from component scores
```

**Key decision**: `DecisionEngine.run()` is a blocking synchronous loop. This is the main entry point for the CLI application (`app.py`).

### 4.2 Market Data (`market_data/`)

```
HyperliquidCollector  ───► OHLCV from Hyperliquid API
    │
    ├── IndicatorEngine   — Technical indicators (EMA, RSI, ATR)
    ├── VolumeEngine      — Volume profile scoring
    ├── BTCHealth         — BTC market health index
    ├── VolatilityEngine  — Volatility classification
    ├── MTFEngine         — Multi-timeframe analysis
    └── LiveEngine        — Real-time market data

    MarketDataNormalizer  — Symbol normalization
    FundingCollector      — Funding rate collection
    OpenInterestCollector — Open interest data
```

### 4.3 Exchange (`exchange/`)

```
ExchangeAdapter (ABC)
├── ticker()
├── candles()
├── account_balance()
├── positions()
├── create_order()
├── cancel_order()
├── order_status()
├── order_history()
└── trading_enabled()

├── HyperliquidConnector — Hyperliquid implementation
└── BinanceConnector     — Binance implementation
```

### 4.4 Execution (`execution/`)

```
ExecutionLoop
├── run_once(signals)        — Process batch, monitor trades
├── process_signal(signal)   — Evaluate → Risk → Size → Create
└── monitor()                — Check open paper trades

DecisionPipeline
├── evaluate(signal)         — Market data → Filters → Score → Confidence
├── _fetch_market_data()     — OHLCV retrieval
├── _passes_filters()        — BTC health gate
└── _validate_signal()       — Required fields check

TradeEngine
└── create_trade()           — TP/SL calcs → DB → Notifications

PaperExecutor
├── open_trade()             — Validate → Persist
├── monitor_open_trades()    — Check all open → TP/SL → Auto-close stale
├── close_trade()            — Manual close with PnL
└── calculate_pnl()          — Unrealized/realized PnL

TPSLEngine
└── calculate()              — Entry/Stop/TP1/TP2/RR from ATR
```

### 4.5 Scoring (`scoring/`)

```
ScoringEngine
└── score(signal)            — 5-component weighted scoring

RegimeAI
└── detect(values)           — Market regime classification

SignalRankingAI
└── rank_signals(signals)    — ML-based signal prioritization

RiskEngine
└── score(values, volatility)— Risk component score

PerformanceIntelligence     — Performance analytics
BacktestV2                  — Historical backtesting
```

### 4.6 API (`api/`)

```
FastAPI Application
├── CORS Middleware
├── Auth Middleware (HTTP)
├── 31 Route Modules
├── 6 WebSocket Endpoints
└── Periodic Broadcast Task (30s)

WebSocket Manager
└── Room-based pub/sub (6 rooms)
```

### 4.7 Database (`database.py` — note: file, not module)

```
Engine (PostgreSQL/SQLite)
│
├── SessionLocal (sessionmaker)
│
├── Models:
│   ├── Signal          — Trading signals
│   ├── Trade           — Executed trades
│   ├── User            — User accounts
│   ├── UserSettings    — User preferences
│   ├── Notification    — Notification records
│   ├── Watchlist       — User watchlists
│   └── JournalEntry    — Trade journal
│
├── Helpers:
│   ├── get_session()   — Session factory
│   ├── session_scope() — Context manager
│   ├── create_tables() — Schema creation
│   └── update_signal_status() — Signal state updates
```

---

## 5. Frontend Architecture

```
App.tsx (Root)
├── ThemeProvider          — Dark theme CSS variables
├── AuthProvider           — Authentication context
├── BrowserRouter
│   └── Routes (31 routes)
│       ├── Login (public)
│       ├── AuthGuard → Layout (protected)
│       │   ├── Header + Sidebar + Outlet
│       │   └── Context:
│       │       ├── WebSocket data (6 rooms)
│       │       └── UI state (Zustand stores)
│       └── NotFound (404)

Page Pattern (per page):
└── useCallback(fetch) → useEffect → loading|error|empty|data → render

State Strategy:
├── React Query — Server state (API data with 10s staleTime)
├── Zustand — Client state (UI, preferences, workspace, terminal)
└── React Context — Auth state, theme
```

---

## 6. Integration Architecture

### Internal Data Channels

```
┌─────────┐    SQLAlchemy     ┌──────────┐
│ Signals │◄──────────────────►│ Database │
│ Trades  │                    │ (SQL)    │
│ Users   │                    └────┬─────┘
└─────────┘                         │
                                    │
┌──────────┐    REST/WS            │
│ Frontend │◄──────────────────────┘
│  (React) │    http://localhost:8000
└──────────┘

┌──────────┐    WebSocket (6 rooms)
│ Frontend │◄────────────────────────┐
│ (Live)   │                         │
└──────────┘    Periodic broadcast   │
                 (every 30s)         │
                                     │
┌─────────────┐    Notification     │
│ Telegram Bot│◄─── Dispatcher      │
└─────────────┘                     │

┌───────────────┐    HTTP API
│ Hyperliquid   │◄──────────────────┘
│ Exchange      │
└───────────────┘
```

---

## 7. Configuration Architecture

```
config.py
├── Environment: API_ENV, DEBUG
├── Database: DATABASE_URL or POSTGRES_*
├── Auth: JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
├── CORS: CORS_ORIGINS
├── Scoring: SCORE_WEIGHTS (5 components)
├── Trading: CHECK_INTERVAL, MIN_SCORE, MAX_OPEN_TRADES
├── Risk: Max exposure, daily loss, position size limits
└── Notifications: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

logging_config.py
├── 3 rotating file handlers (10MB, 5 backups)
├── 1 console handler (JSON in prod, plain in dev)
└── log_state() structured logging helper

startup.py
├── Environment validation
├── PostgreSQL configuration check
├── Config sanity check
├── Database connectivity check
└── Table accessibility check
```

---

## 8. Deployment Architecture

### Development (docker-compose.yml)

```
┌─────────┐   ┌─────────┐   ┌──────────┐
│PostgreSQL│   │  Redis  │   │   API    │
│  16      │   │   7     │   │uvicorn   │
│:5432     │   │:6379    │   │:8000     │
└─────────┘   └─────────┘   └──────────┘
```

### Production (docker-compose.prod.yml)

```
Internet
    │
    ▼
┌──────────┐  Let's Encrypt TLS
│  Traefik │◄─────────────────────
│  v3.0    │
└────┬─────┘
     │
     ├── api.elite-decision.io ──► FastAPI (4 workers, 1000 concurrency)
     ├── app.elite-decision.io ──► Nginx (SPA)
     └── monitor.elite-decision.io ──► Grafana

Internal Network:
├── PostgreSQL 16 (persistent)
├── Redis 7 (password auth)
├── Prometheus (30d retention)
└── Backup (cron → S3)
```

---

*End of ARCHITECTURE.md*
