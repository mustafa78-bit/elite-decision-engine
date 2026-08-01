# DEPENDENCY GRAPH — Elite Decision Engine

> Complete dependency map showing imports, relationships, and coupling between all modules.

---

## 1. Module Dependency Matrix

```
MODULE               DEPENDS ON                                         DEPENDED ON BY
───                  ──────────                                         ─────────────
core/engine          database, execution/execution_loop, config          app.py
core/confidence      scoring/scoring_engine                              execution/pipeline
execution/pipeline   core/confidence, filters, memory, scoring/*        execution/execution_loop
execution/l loop     execution/pipeline, risk_manager, pos_sizing       core/engine
execution/trade_engine database, execution/tp_sl, notifications/*       execution/execution_loop
execution/paper_exec database, market_data/collector, notifications/*   execution/execution_loop
execution/tp_sl      (standalone)                                       execution/trade_engine
scoring/scoring_eng  market_data/*                                       execution/pipeline, api/main
scoring/regime_ai    (standalone)                                        execution/pipeline, api/main
scoring/signal_rnk   (standalone)                                        execution/execution_loop
scoring/risk_engine  (standalone)                                        scoring/scoring_engine, api/main
market_data/collect  pandas, httpx                                       execution/pipeline, scoring/engine
market_data/indic    pandas-ta                                           scoring/scoring_engine
market_data/volume   pandas                                              scoring/scoring_engine
market_data/btc_hlth pandas                                              scoring/scoring_engine, api/main
market_data/volatil  pandas                                              scoring/scoring_engine, api/main
market_data/mtf      pandas, market_data/collector                       scoring/scoring_engine
database.py          sqlalchemy, config                                  EVERYTHING
api/main             api/*, monitoring, config, database                 Docker CMD
api/routes/*         database, services/*                                api/main
api/websocket/*      fastapi                                             api/main
services/*           database                                            api/routes/*
exchange/base        exchange/models                                     exchange/hyperliquid, binance
exchange/hyperliquid exchange/base, exchange/exceptions                  api/main (indirect)
exchange/binance     exchange/base, exchange/exceptions                  api/main (indirect)
notifications/*      database                                            execution/*, api/*
risk/*               database, exchange/models                           api/routes
shadow/*             exchange/*                                          api/main
simulator/*          exchange/*                                          api/main
strategies/*         scoring/*                                           api/main
```

---

## 2. Import Dependency Graph

```
app.py
  └── core/engine.py
        ├── database.py
        │     ├── config.py
        │     └── sqlalchemy
        └── execution/execution_loop.py
              ├── database.py
              ├── execution/pipeline.py
              │     ├── core/confidence_engine.py
              │     │     └── scoring/scoring_engine.py
              │     │           ├── market_data/collector.py  ←── Hyperliquid API (HTTP)
              │     │           ├── market_data/indicators.py
              │     │           ├── market_data/volume.py
              │     │           ├── market_data/btc_health.py
              │     │           ├── market_data/volatility.py
              │     │           ├── market_data/mtf.py
              │     │           │     └── market_data/collector.py
              │     │           └── scoring/risk_engine.py
              │     ├── filters/btc_filter.py
              │     ├── memory/trade_memory.py
              │     ├── scoring/regime_ai.py
              │     └── market_data/collector.py
              ├── execution/paper_executor.py
              │     ├── database.py
              │     ├── market_data/collector.py
              │     └── notifications/dispatcher.py
              ├── execution/trade_engine.py
              │     ├── database.py
              │     ├── execution/tp_sl.py
              │     └── notifications/dispatcher.py
              ├── risk_manager.py
              ├── position_sizing.py
              └── scoring/signal_ranking_ai.py

api/main.py
  ├── api/routes/auth.py
  │     └── auth/service.py
  │           ├── auth/jwt.py
  │           └── database.py
  ├── api/routes/* (31 routers)
  │     └── services/* (9 services)
  │           └── database.py
  ├── api/websocket/manager.py
  ├── monitoring/health.py
  │     ├── database.py
  │     ├── market_data/collector.py
  │     ├── market_data/indicators.py
  │     └── market_data/btc_health.py
  ├── market_data/* (collector, indicators, btc_health, volatility)
  ├── scoring/regime_ai.py
  └── scoring/risk_engine.py
```

---

## 3. Circular Dependency Analysis

```
No circular dependencies detected.

Analysis method: Each module was checked for import cycles.
The architecture enforces strict layering:
  Core → Execution → Database     (downward)
  API → Services → Database       (downward)
  Scoring → Market Data           (downward)
  Execution → {Pipeline, Risk, Notifications}  (fan-out, no cycles)
```

---

## 4. Coupling Analysis

### High Cohesion Modules (Good)
| Module | Internal Cohesion | Description |
|--------|------------------|-------------|
| `execution/paper_executor.py` | HIGH | All paper trade lifecycle in one file |
| `scoring/regime_ai.py` | HIGH | Self-contained regime detection |
| `execution/pipeline.py` | HIGH | Pipeline orchestrates but doesn't execute |
| `exchange/base.py` | HIGH | Clean abstract interface |

### High Coupling Modules (Risk)
| Module | Coupling Level | Risk |
|--------|---------------|------|
| `api/main.py` | VERY HIGH | Imports 20+ modules directly |
| `execution/execution_loop.py` | HIGH | Depends on 8+ modules |
| `execution/pipeline.py` | HIGH | Depends on 6+ modules |
| `scoring/scoring_engine.py` | HIGH | Depends on 5 market data modules + risk |

### Low Coupling Modules (Good)
| Module | Fan-Out | Description |
|--------|---------|-------------|
| `execution/tp_sl.py` | 0 | Standalone calculator |
| `filters/btc_filter.py` | 1 | Depends only on collector |
| `memory/trade_memory.py` | 1 | Depends only on database |
| `exchange/hyperliquid/connector.py` | 1 | Depends only on base adapter |

---

## 5. External Dependency Map

### Python Runtime Dependencies

```
bcrypt              ── Used by auth (password hashing)
fastapi             ── Web framework (API layer)
httpx               ── HTTP client (exchange connectors)
pandas              ── Data processing (scoring engines)
pandas-ta           ── Technical indicators
psycopg2-binary     ── PostgreSQL driver
PyJWT               ── JWT authentication
python-dotenv       ── Environment loading
requests            ── Legacy HTTP client (not used by core modules)
sqlalchemy          ── ORM (database layer)
starlette           ── ASGI framework (FastAPI dependency)
uvicorn             ── ASGI server
websockets          ── WebSocket protocol
```

### Frontend Runtime Dependencies

```
react               ── UI framework
react-dom           ── DOM rendering
react-router-dom    ── Routing
zustand             ── State management
@tanstack/react-query ── Server state
react-hook-form     ── Form handling
zod                 ── Schema validation
framer-motion       ── Animations
lightweight-charts  ── Trading charts
recharts            ── Data charts
clsx                ── Class name utility
```

### Infrastructure Dependencies

```
PostgreSQL 16       ── Database
Redis 7             ── Cache/message broker
Traefik v3          ── Reverse proxy/TLS
Nginx               ── Web server (SPA)
Prometheus          ── Metrics
Grafana             ── Dashboards
```

---

## 6. File-Level Import Map (Key Modules)

### `execution/execution_loop.py`
```
Imports:
  database                     → update_signal_status, Signal, Trade
  execution/paper_executor     → PaperExecutor, TradeMonitorResult
  execution/pipeline           → DecisionPipeline, TradeCandidate, TradingSignal
  execution/trade_engine       → TradeEngine
  position_sizing              → PositionSizingEngine
  risk_manager                 → RiskManager
  scoring/signal_ranking_ai    → SignalRankingAI
```

### `execution/pipeline.py`
```
Imports:
  core/confidence_engine       → ConfidenceEngine
  filters/btc_filter           → BTCHealthFilter
  market_data/collector        → HyperliquidCollector
  memory/trade_memory          → TradeMemory
  scoring/regime_ai            → RegimeAI
  scoring/scoring_engine       → ScoringEngine
```

### `api/main.py`
```
Imports (20+):
  api.events, api.middleware, api.websocket.manager
  api.routes.auth, backtest, execution, intelligence, journal, market, ...
  monitoring.health
  config (API_ENV, CORS_ORIGINS, DEBUG)
  database (FINAL_STATUSES, Trade, get_session)
  market_data.* (btc_health, collector, indicators, volatility)
  scoring.* (regime_ai, risk_engine)
```

---

## 7. Shared Utility Dependencies

```
config.py
  ├── python-dotenv
  └── os.environ
  │
  ├── Read by: database.py, startup.py, api/main.py, api/middleware.py
  ├── Read by: logging_config.py, app.py
  └── Read by: position_sizing.py, risk_manager.py

database.py
  ├── sqlalchemy (engine, session, models)
  └── config
  │
  ├── Used by: 40+ modules across the codebase
  └── THE MOST DEPENDENT-UPON MODULE IN THE SYSTEM

logging_config.py
  ├── logging (stdlib)
  └── config
  │
  └── Used by: app.py (called once at startup)

startup.py
  ├── config
  ├── database
  └── Used by: app.py, api/main.py (shutdown)
```

---

## 8. Dependency Recommendations

### High Priority
| Issue | Impact | Fix |
|-------|--------|-----|
| `database.py` is a monolith | Any schema change affects 40+ modules | Split into models/ + session/ |
| `api/main.py` imports 20+ modules | High coupling, slow startup | Use lazy imports or registry pattern |
| `scoring_engine.py` fetches market data directly | Duplicate fetch in pipeline + scoring | Pass pre-fetched data as parameter |

### Medium Priority
| Issue | Impact | Fix |
|-------|--------|-----|
| No formal interface between `execution` and `notifications` | Tight coupling to dispatcher | Add notification protocol |
| Config is a flat module | No validation, no typing | Use pydantic-settings |
| Market data modules tightly coupled within `score()` | Hard to mock/test individually | Add interface protocols for each sub-engine |

---

*End of DEPENDENCY_GRAPH.md*
