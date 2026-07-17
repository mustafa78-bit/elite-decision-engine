# Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Elite Decision Engine                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │   API Layer   │    │   Core Services  │    │  Intelligence    │  │
│  │  (api/)       │    │   (core/)        │    │  Modules         │  │
│  │              │    │                  │    │                  │  │
│  │  APIApp      │───▶│  DecisionEngine  │───▶│  Whale           │  │
│  │  Router      │    │  HealthChecker   │    │  Liquidity       │  │
│  │  Schemas     │    │  DashboardSvc    │    │  OrderFlow       │  │
│  │  Errors      │    │  TTLCache        │    │  MarketStruct    │  │
│  │  Middleware  │    │  Scheduler       │    │  News            │  │
│  │  WebSocket   │    │  RetryHandler    │    │  Sentiment       │  │
│  │              │    │  ConfigValidator │    │  Macro           │  │
│  └──────┬───────┘    └────────┬─────────┘    └──────────────────┘  │
│         │                     │                                     │
│         ▼                     ▼                                     │
│  ┌──────────────┐    ┌──────────────────┐                           │
│  │  DTO Layer   │    │  Decision        │                           │
│  │  (dto/)      │    │  Pipeline        │                           │
│  │              │    │  (decision/)     │                           │
│  │  Portfolio   │    │                  │                           │
│  │  Trade       │    │  TradeMemory     │                           │
│  │  Intelligence│    │  Intelligence    │                           │
│  │  Risk        │    │  Fusion          │                           │
│  │  Monitoring  │    │  Confidence      │                           │
│  │  Notification│    │  Engine          │                           │
│  └──────────────┘    └──────────────────┘                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Persistence                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐  │   │
│  │  │  database.py │  │  config.py  │  │  TradeMemoryStore    │  │   │
│  │  │  SQLAlchemy  │  │  .env vars  │  │  (in-memory)         │  │   │
│  │  └─────────────┘  └─────────────┘  └──────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Cross-cutting                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │   │
│  │  │ Filters  │  │ Scoring  │  │Execution │  │  External     │  │   │
│  │  │(filters/)│  │(scoring/)│  │(execution│  │  Integrations │  │   │
│  │  │  BTC     │  │  Engine  │  │  Bridge) │  │  (whale/,     │  │   │
│  │  │  Shock   │  │          │  │          │  │  news/, etc)  │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Signal → DecisionEngine → IntelligenceBundle → Module Evaluation
                                                  │
                   ┌──────────────────────────────┘
                   ▼
             Fusion Engine
                   │
                   ▼
             DecisionRouter → APIApp → Frontend
                   │
                   ▼
             WSManager → WebSocket → Real-time Clients
```

## Module Dependencies

```
api/   ──▶  core/  ──▶  decision/  ──▶  modules/
  │              │                      │
  ▼              ▼                      ▼
dto/          cache/                 whale/, liquidity/,
              health/                orderflow/,
              validation/            market_structure/,
              serialization/         news/, sentiment/,
                                    macro/
```
