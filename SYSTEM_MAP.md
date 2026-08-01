# SYSTEM MAP — Elite Decision Engine

> Complete component inventory and mapping of every module in the system.

---

## 1. Layer Map

```
LAYER 1: DATA SOURCES
├── Hyperliquid API (OHLCV, funding, OI)
├── Binance API (market data)
├── PostgreSQL (persistent storage)
└── Redis (caching — configured but not used for caching)

LAYER 2: DATA INGESTION
├── HyperliquidCollector         market_data/collector.py
├── FundingCollector             market_data/funding/collector.py
├── OpenInterestCollector        market_data/open_interest/collector.py
├── LiveMarketEngine             market_data/live/engine.py
└── MarketDataNormalizer         market_data/normalizer/

LAYER 3: COMPUTATION ENGINE
├── IndicatorEngine              market_data/indicators.py
├── VolumeEngine                 market_data/volume.py
├── BTCHealth                    market_data/btc_health.py
├── VolatilityEngine             market_data/volatility.py
├── MTFEngine                    market_data/mtf.py
├── ScoringEngine                scoring/scoring_engine.py
├── RiskEngine                   scoring/risk_engine.py
├── RegimeAI                     scoring/regime_ai.py
├── RegimeEngine                 scoring/regime_engine.py
├── ConfidenceEngine             core/confidence_engine.py
├── PerformanceIntelligence      scoring/performance_intelligence.py
└── SignalRankingAI              scoring/signal_ranking_ai.py

LAYER 4: DECISION ORCHESTRATION
├── DecisionEngine               core/engine.py
├── ExecutionLoop                execution/execution_loop.py
├── DecisionPipeline             execution/pipeline.py
├── RiskManager                  risk_manager.py
├── PositionSizingEngine         position_sizing.py
└── TradeEngine                  execution/trade_engine.py

LAYER 5: EXECUTION
├── PaperExecutor                execution/paper_executor.py
├── TPSLEngine                   execution/tp_sl.py
├── ShadowEngine                 shadow/shadow_engine.py
├── ExecutionSimulator           simulator/execution_simulator.py
├── OrderManager                 orders/order_manager.py
└── ExecutionGuard               risk/execution_guard.py

LAYER 6: EXCHANGE ADAPTERS
├── ExchangeAdapter (ABC)        exchange/base.py
├── HyperliquidConnector         exchange/hyperliquid/connector.py
└── BinanceConnector             exchange/binance/connector.py

LAYER 7: API (REST + WebSocket)
├── FastAPI Application          api/main.py
├── Auth Middleware               api/middleware.py
├── 31 Route Modules             api/routes/*.py
├── WebSocket Manager            api/websocket/manager.py
├── Event Handlers               api/events.py
└── Cache Layer                  api/cache.py

LAYER 8: SERVICES
├── AnalyticsService             services/analytics_service.py
├── CoordinatorService           services/coordinator_service.py
├── ExplanationService           services/explanation_service.py
├── KpiService                   services/kpi_service.py
├── NotificationService          services/notification_service.py
├── PortfolioService             services/portfolio_service.py
├── PreferencesService           services/preferences_service.py
├── TimelineService              services/timeline_service.py
├── WatchlistService             services/watchlist_service.py
└── WidgetService                services/widget_service.py

LAYER 9: INFRASTRUCTURE
├── StartupValidator             startup.py
├── LoggingConfig                logging_config.py
├── Config                       config.py
├── HealthService                monitoring/health.py
├── PortfolioEngine              portfolio_engine.py
├── PerformanceEngine            performance_engine.py
├── TradeMemory                  memory/trade_memory.py
├── NotificationDispatcher       notifications/dispatcher.py
├── NotificationSerializer       notifications/serializer.py
├── FeatureStore                 features/store.py
└── BTCFilter                    filters/btc_filter.py

LAYER 10: PRESENTATION (Frontend)
├── 33 Pages                     frontend/src/pages/
├── 200+ Components              frontend/src/components/
├── 5 Zustand Stores             frontend/src/stores/
├── 6 Custom Hooks               frontend/src/hooks/
├── 17 API Modules               frontend/src/api/
├── WebSocket Client             frontend/src/websocket/
├── 8 Type Definition Files      frontend/src/types/
├── 2 CSS Token Files            frontend/src/styles/
└── 20 Test Files                frontend/src/test/
```

---

## 2. Database Entity Map

```
┌─────────────────────────────────────────────────────────────┐
│                     DATABASE (PostgreSQL/SQLite)            │
│                                                             │
│  signals                                                    │
│  ├── id (PK) ◄──────────────────────────────────────────┐  │
│  ├── symbol, side, timeframe                             │  │
│  ├── score, confidence, status                           │  │
│  ├── market_health, btc_health                          │  │
│  ├── volume_score, funding_score, oi_score               │  │
│  ├── cvd_score, trend_score, risk_score                 │  │
│  └── approved, reason, created_at                        │  │
│                                                          │  │
│  trades ◄────────────────────────────────────────────────┘  │
│  ├── id (PK)                                                │
│  ├── signal_id (FK → signals.id)                            │
│  ├── symbol, side, entry, stop, tp1, tp2, rr                │
│  ├── pnl, status, exit_price, closed_at, close_reason       │
│  └── exchange_order_id, created_at                          │
│                                                             │
│  users                                                      │
│  ├── id (PK)                                                │
│  ├── username, email, hashed_password                       │
│  └── created_at, updated_at                                 │
│                                                             │
│  user_settings ──── FK → users.id                           │
│  ├── timezone, theme                                        │
│  ├── dashboard_config (JSON)                                │
│  ├── risk_preferences (JSON)                                │
│  ├── layout_config (JSON)                                   │
│  └── notification_preferences (JSON)                        │
│                                                             │
│  notifications ──── FK → users.id (optional)                │
│  ├── event_type, payload (JSON), read                       │
│  └── created_at                                             │
│                                                             │
│  watchlists ──── FK → users.id (optional)                   │
│  ├── name, symbols (JSON)                                   │
│  └── created_at, updated_at                                 │
│                                                             │
│  journal_entries                                            │
│  ├── symbol, side, entry_price, exit_price                  │
│  ├── score, confidence, result, pnl                         │
│  ├── entry_reason, exit_reason, notes                       │
│  ├── signal_id (FK → signals.id, optional)                  │
│  ├── trade_id (FK → trades.id, optional)                    │
│  └── created_at                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. API Endpoint Map

```
METHOD  PATH                          MODULE              FILE
──────  ────                          ──────              ────
ANY     /auth/*                        auth                routes/auth.py
ANY     /execution/*                   execution           routes/execution.py
ANY     /signals/*                     signals             routes/signals.py
ANY     /signals/ranking/*             signals_ranking     routes/signals_ranking.py
ANY     /trading-control/*             trading_control     routes/trading_control.py
ANY     /market/*                      market              routes/market.py
ANY     /market/live/*                 market_live         routes/market_live.py
ANY     /portfolio/*                   portfolio           routes/portfolio.py
ANY     /portfolio/update/*            portfolio_detail    routes/portfolio_detail.py
ANY     /risk/*                        risk                routes/risk.py
ANY     /regime/*                      regime              routes/regime.py
ANY     /analytics/*                   analytics           routes/analytics.py
ANY     /kpi/*                         kpi                 routes/kpi.py
ANY     /dashboard/*                   dashboard           routes/dashboard.py
ANY     /widgets/*                     widgets             routes/widgets.py
ANY     /notifications/*               notifications       routes/notifications.py
ANY     /paper-trading/*               paper_trading       routes/paper_trading.py
ANY     /performance/*                 performance         routes/performance.py
ANY     /backtest/*                    backtest            routes/backtest.py
ANY     /journal/*                     journal             routes/journal.py
ANY     /intelligence/*                intelligence        routes/intelligence.py
ANY     /explanation/*                 explanation         routes/explanation.py
ANY     /coordination/*                coordination        routes/coordination.py
ANY     /monitoring/*                  monitoring          routes/monitoring.py
ANY     /preferences/*                 preferences         routes/preferences.py
ANY     /watchlists/*                  watchlists          routes/watchlists.py
ANY     /timeline/*                    timeline            routes/timeline.py
ANY     /users/*                       users               routes/users.py
GET     /health                        (main)              api/main.py
WS      /ws/trades                     (main)              api/main.py
WS      /ws/analytics                  (main)              api/main.py
WS      /ws/dashboard                  (main)              api/main.py
WS      /ws/portfolio                  (main)              api/main.py
WS      /ws/notifications              (main)              api/main.py
WS      /ws/preferences                (main)              api/main.py
```

---

## 4. Frontend Route Map

```
PATH                            PAGE COMPONENT           FILE
────                            ──────────────           ────
/login                          LoginPage                pages/LoginPage.tsx
/overview                       Overview                 pages/Overview.tsx
/dashboard                      Dashboard                pages/Dashboard.tsx
/trades                         Trades                   pages/Trades.tsx
/timeline                       TimelinePage             pages/TimelinePage.tsx
/watchlists                     WatchlistsPage           pages/WatchlistsPage.tsx
/portfolio-detail               PortfolioDetailPage      pages/PortfolioDetailPage.tsx
/market                         Market                   pages/Market.tsx
/notifications                  NotificationsPage        pages/Notifications.tsx
/portfolio                      Portfolio                pages/Portfolio.tsx
/signals                        Signals                  pages/Signals.tsx
/signals/ranking                SignalsRanking           pages/SignalsRanking.tsx
/risk                           Risk                     pages/Risk.tsx
/regime                         Regime                   pages/Regime.tsx
/analytics                      Analytics                pages/Analytics.tsx
/paper-trading                  PaperTrading              pages/PaperTrading.tsx
/execution                      Execution                pages/Execution.tsx
/intelligence                   Intelligence             pages/Intelligence.tsx
/live-market                    LiveMarket               pages/LiveMarket.tsx
/trading-control                TradingControl           pages/TradingControl.tsx
/journal                        Journal                  pages/Journal.tsx
/backtest                       Backtest                 pages/Backtest.tsx
/preferences                    PreferencesPage           pages/PreferencesPage.tsx
/funding                        FundingPage               pages/FundingPage.tsx
/open-interest                  OpenInterestPage          pages/OpenInterestPage.tsx
/whale                          WhalePage                 pages/WhalePage.tsx
/liquidity                      LiquidityPage             pages/LiquidityPage.tsx
/hero-dashboard                 HeroDashboard             pages/HeroDashboard.tsx
/trading-workspace              TradingWorkspace          pages/TradingWorkspace.tsx
/ai-experience                  AIExperience              pages/AIExperience.tsx
/professional-workspace         ProfessionalWorkspace     pages/ProfessionalWorkspace.tsx
*                               NotFound                  pages/NotFound.tsx
```

---

## 5. WebSocket Channel Map

```
CHANNEL         EVENTS                              FREQUENCY
───────         ──────                              ─────────
/ws/trades      TRADE_OPENED, TRADE_CLOSED           Event-driven + 30s periodic
/ws/analytics   Analytics data push                  30s periodic
/ws/dashboard   Dashboard state update               30s periodic
/ws/portfolio   Portfolio summary push               30s periodic
/ws/notifications Notification events                Event-driven + 30s periodic
/ws/preferences Preference sync                      30s periodic

BROADCAST PAYLOADS (from _periodic_broadcast, every 30s):
├── MarketEvent       → price, regime, btc_health_score, volatility
├── PriceUpdateEvent  → symbol, price, volume
├── CandleUpdateEvent → symbol, OHLCV, timestamp
├── VolumeUpdateEvent → symbol, volume_24h
└── RiskEvent         → risk_score, open_trades, max_open_trades, daily_loss, max_daily_loss
```

---

## 6. Scoring Component Map

```
SCORING_ENGINE.score(signal)
│
├── Component 1: TREND (weight: 0.30)
│   ├── EMA20 vs EMA50 alignment (+0.5 if aligned)
│   └── EMA50 vs EMA200 alignment (+0.5 if aligned)
│
├── Component 2: VOLUME (weight: 0.20)
│   └── VolumeEngine.score() → volume profile analysis
│
├── Component 3: BTC (weight: 0.20)
│   └── BTCHealth.score() → BTC market health index
│
├── Component 4: MTF (weight: 0.20)
│   └── MTFEngine.score() → multi-timeframe alignment
│
└── Component 5: RISK (weight: 0.10)
    └── RiskEngine.score() → risk assessment

FINAL_SCORE = Σ(component_score × weight)

DECISION_THRESHOLDS:
├── APPROVE        → final_score >= 0.85 (configurable via MIN_SCORE)
├── STRONG_APPROVE → final_score >= 0.95
└── REJECT         → final_score < 0.85
```

---

## 7. Infrastructure Map

```
NAME            TYPE            FILE
────            ────            ────
Dockerfile      Build Stage 1  Dockerfile (Node 22 → frontend build)
                Build Stage 2  Dockerfile (Python 3.12 → runtime)
Dockerfile.prod Build Stage 1  Dockerfile.prod (Node 22 → frontend build)
                Build Stage 2  Dockerfile.prod (Python 3.12 → deps)
                Build Stage 3  Dockerfile.prod (Python 3.12 → runtime, non-root)
Dockerfile.arm64 ARM64 variant Dockerfile.arm64
docker-compose.yml  Dev        Postgres 16 + Redis 7 + API
docker-compose.prod.yml Prod   Traefik + Postgres + Redis + API + Nginx + Prometheus + Grafana + Backup
.github/workflows/ci.yml CI    Python lint + test, Node build
deploy/nginx.conf   Config     Nginx SPA config with security headers
```

---

## 8. Test File Map

```
TEST SUITE          FILES                    COVERS
──────────          ─────                    ──────
Execution Tests     8 files                  Pipeline, Loop, Trade Engine, Paper Executor, TP/SL
Scoring Tests       8 files                  Scoring, Risk, Regime AI, Signal Ranking, Backtest, Performance
Market Data Tests   8 files                  Indicators, Collector, Volatility, Volume, MTF, BTC, Funding, OI
API Tests           12 files                 Auth, Analytics, Coordinator, Dashboard, Execution, etc.
Exchange Tests      4 files                  Base, Binance, Hyperliquid, Models
Infrastructure      8 files                  Auth, Notifications, WebSocket, Order Manager
Integration Tests   4 files                  E2E, Edge Cases, Batch
Frontend Tests      20 files                 Components, API, Pages
```

---

*End of SYSTEM_MAP.md*
