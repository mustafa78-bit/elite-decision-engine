# Chapter 03: Repository Structure

## 📂 Repository File & Directory Map
The NEXUS repository layout represents a clean, modular structure. Below is a comprehensive tree mapping the directories and major files discussed throughout this Master Memory Book.

```
.
├── api/                           # FastAPI Router & WebSocket endpoints
│   ├── routes/                    # Subsystem specific routers (auth, market, trade, etc.)
│   ├── websocket/                 # Real-time WebSocket connection manager and rooms
│   ├── main.py                    # API entry point & lifespan orchestrator
│   ├── middleware.py              # Auth (JWT) & Logging Interceptors
│   └── rate_limit.py              # API slowapi-based request rate limiting
├── auth/                          # Cryptographic & Session Token engines
│   ├── jwt.py                     # HS256 JWT encoding, decoding, validation
│   └── service.py                 # Password hashing & User Verification
├── core/                          # Fundamental core engines
│   ├── engine.py                  # Core signal ingestion scheduler
│   └── confidence_engine.py       # Algorithmic signal confidence assessor
├── council/                       # AI Council Multi-Agent System
│   ├── base.py                    # Base agent interface and debate contracts
│   ├── consensus.py               # Direction & Weight consensus aggregator
│   ├── trend_agent.py             # Specialized Trend-following analyst
│   ├── technical_agent.py         # Specialized Technical Indicator analyst
│   ├── risk_agent.py              # Specialized Risk and draw-down protector
│   ├── whale_agent.py             # Specialized Large Order & CVD tracker
│   ├── news_agent.py              # Specialized Sentiment Analyst stub
│   └── macro_agent.py             # Specialized Macro market context agent
├── decision/                      # Explainable intelligence subsystem
│   ├── evidence/                  # Evidence registry, builders, conflict detector
│   ├── aggregator.py              # Gathers multidisciplinary evidence
│   ├── confidence_v2.py           # Enhanced secondary confidence scoring
│   ├── explanation.py             # Translates scores to natural language explanations
│   ├── timeline.py                # Auditable cognitive trace ledger
│   └── models.py                  # SQL-ORM mapping schemas for explanations
├── deploy/                        # Infrastructure deployment files
│   └── nginx.conf                 # Gateway routing and WebSocket proxying
├── dto/                           # Data Transfer Objects for route payloads
├── exchange/                      # Exchange interface adapters (Hyperliquid, Binance)
├── execution/                     # Trading execution engine and paper simulator
│   ├── execution_loop.py          # Master batch loop coordinator
│   ├── pipeline.py                # Protocol-based data collection & processing
│   ├── trade_engine.py            # TP/SL, duplicate guards, and trade creation
│   ├── paper_executor.py          # Monitors, ticks, and terminates paper trades
│   ├── paper.py                   # Paper Trading routing interface
│   └── tp_sl.py                   # ATR-based entry/stop/profit engines
├── explain/                       # Legacy explainability stubs
├── features/                      # Machine Learning Feature Stores
├── filters/                       # High-level Signal guards and market filters
│   └── btc_filter.py              # BTC health-based long/short filter
├── market/                        # Unified Market Intelligence Platform
│   ├── cache/                     # Volatile feature caches & managers
│   ├── context/                   # Multi-instrument order contexts
│   ├── features/                  # Live dynamic indicators and feature stores
│   ├── indicators/                # Quantitative signal computations
│   ├── intelligence/              # Whale, news, funding, flow metrics
│   ├── models/                    # Asset metadata and OHLCV schemas
│   ├── provider/                  # Exchange-specific websockets & REST wrappers
│   └── services/                  # Aggregate MarketDataService coordinator
├── market_data/                   # Legacy raw collection loops and collectors
├── memory/                        # Permanent and ephemeral knowledge layers
│   └── trade_memory.py            # Local trade state & context repository
├── monitoring/                    # Platform status telemetry and metrics
│   └── health.py                  # Service uptime and platform health trackers
├── notifications/                 # Real-time Webhook & Telegram Dispatchers
│   ├── dispatcher.py              # Routes notifications to correct mediums
│   └── events.py                  # Typed schemas for trade events
├── orders/                        # Order management stubs
├── performance/                   # Performance calculation core
│   ├── core.py                    # Standard ratios (Sharpe, Sortino, Calmar)
│   └── engine.py                  # Performance calculation engine
├── portfolio/                     # High-level portfolio asset aggregators
│   └── core.py                    # Portfolio equity, drawdowns, exposures
├── risk/                          # Real-time Execution Guards
│   ├── execution_guard.py         # Pre-flight signal validations
│   └── models.py                  # Risk check structures & Rejection codes
├── scanner/                       # Live multi-strategy scanner core
│   └── strategies/                # Technical strategies (trend, breakout, rsi)
├── scoring/                       # Machine Learning & Multi-Factor Scoring
│   ├── scoring_engine.py          # 5-factor weighted core signal scorer
│   ├── signal_ranking_ai.py       # ML-based signal ranker
│   └── regime_ai.py               # Market regime classifier (ranging, trending)
├── services/                      # Higher-level orchestration services
│   ├── ollo/                      # OLLO natural-language executive briefing
│   ├── coordinator_service.py     # Central service orchestration register
│   ├── explanation_service.py     # Unified interface for explanations
│   ├── portfolio_service.py       # Unified portfolio analytics manager
│   └── widget_service.py          # High-density dashboard widgets formatter
├── shadow/                        # Shadow live-trading configurations
├── simulator/                     # Market simulation stubs
├── strategies/                    # Quantitative trading strategy stubs
├── tests/                         # Complete test suite mapping 1,326 test cases
├── utils/                         # Global helpers and security scripts
├── database.py                    # Global SQLAlchemy models & Connection Pools
├── config.py                      # Strongly-typed environment schema config
├── Dockerfile                     # Main containerization configuration
├── Dockerfile.prod                # Production optimized containerization
└── pyproject.toml                 # Poetry package dependency manifest
```

---

## 🏗️ Architectural Layer Boundaries & Separation of Concerns

NEXUS enforces strict logical boundaries across layers to ensure a senior developer can easily modify individual algorithms without breaking system integrity.

### 1. Data Layer (`database.py`, `market/models/`)
This is the lowest layer of the platform, dealing strictly with data definitions and persistence. No trading logic or intelligence computations reside here. Models are pure SQLAlchemy declarative base objects.

### 2. Integration Layer (`exchange/`, `market/provider/`)
Deals with third-party protocol conversions, WebSockets parsing, and HTTP requests to Hyperliquid and Binance APIs. All API payloads are immediately normalized into platform-standard Data Transfer Objects (DTOs) or market models before passing up.

### 3. Computation & Intelligence Layer (`scoring/`, `council/`, `decision/`)
This layer is entirely deterministic, stateless, and dependency-injection friendly. It receives normalized market contexts and signals, processes them through quantitative models (5-factor scorers, AI Council, indicators), and outputs scored recommendations.

### 4. Orchestration Layer (`core/`, `execution/`, `services/`)
Coordinates the pipeline execution. It grabs signals from the database, sends them to the computation layer, pipes the results to the risk layer, forwards passing signals to the trade engine, and monitors open paper transactions. It acts as the glue linking the API, database, intelligence engines, and exchange adapters.

### 5. API Router & Presentation Layer (`api/`, `frontend/`)
The interface boundary. Exposes RESTful endpoints, handles HTTP validations, maps data to widget-specific response objects, authenticates user tokens, and pumps real-time events over WebSocket connections.
