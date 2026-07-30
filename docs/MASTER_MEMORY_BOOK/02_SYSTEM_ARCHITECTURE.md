# Chapter 02: System Architecture

## 🌐 Macro-Scale System Topology
NEXUS is designed as a decoupled, high-throughput, dual-layer system featuring a **Python FastAPI backend** and a **React 19 single-page-application frontend**. Real-time bi-directional messaging is maintained via multiplexed **WebSockets**, enabling instantaneous delivery of market telemetry, risk metrics, and order updates to the UI.

The platform's logical architecture consists of three distinct horizontal tiers:
1. **Telemetry & Data Collection Tier**: Polls live exchange adapters, normalizes data feeds (funding rates, open interest, order book depth, OHLCV candles), and populates cache layers and databases.
2. **Cognitive & Decision Tier**: Orchestrates multiple specialized AI agents, runs them through debate loops, evaluates signals via a multi-component scoring pipeline, and performs real-time risk checks.
3. **Execution & Simulation Tier**: Manages the life cycle of paper trades, orders, and positions, applying rigorous automated stop-loss (SL) and take-profit (TP) monitoring.

---

## 📊 System Topology Diagram

```mermaid
graph TD
    subgraph Client Tier [Frontend - React 19]
        UI[Command Deck HUD]
        WS_Client[WS Manager Client]
        Store[Zustand & React Query Stores]
        UI --> Store
        WS_Client -.-> Store
    end

    subgraph API & Gateway Tier [Backend - FastAPI]
        FastAPI_App[FastAPI Application]
        Auth_MW[JWT Auth Middleware]
        Security_MW[Security Headers Middleware]
        WS_Server[WebSocket Manager Server]

        FastAPI_App --> Auth_MW
        FastAPI_App --> Security_MW
        FastAPI_App --> WS_Server
    end

    subgraph Cognitive & Intelligence Tier
        Orchestrator[ExecutionLoop & Orchestrator]
        DecPipeline[DecisionPipeline]
        AICouncil[AI Council Debate Engine]
        Evidence[Evidence Engine]
        RiskGuard[Risk Engine / ExecutionGuard]

        Orchestrator --> DecPipeline
        DecPipeline --> AICouncil
        DecPipeline --> Evidence
        DecPipeline --> RiskGuard
    end

    subgraph Persistence & Caching Tier
        DB[(PostgreSQL / SQLite DB)]
        Cache[Ephemeral Caches / FeatureStore]
    end

    subgraph Market & Exchange Tier
        MIP_Service[MarketDataService]
        HL_Adapter[Hyperliquid Adapter]
        Binance_Adapter[Binance Adapter]

        MIP_Service --> HL_Adapter
        MIP_Service --> Binance_Adapter
    end

    %% Data Connections
    Store <--> |REST HTTP| FastAPI_App
    WS_Client <--> |WebSocket Multiplex| WS_Server
    FastAPI_App --> DB
    FastAPI_App --> Cache
    Orchestrator --> DB
    Orchestrator --> Cache
    Orchestrator --> MIP_Service
    WS_Server -.-> |Push Updates| WS_Client
```

---

## 🔄 End-to-End Decision & Signal Lifecycle

The lifecycle of a signal is executed through a highly structured, step-by-step pipeline. The following sequence diagram illustrates how a raw signal gets processed, debated by the AI Council, evaluated by the risk engines, executed, and monitored:

```mermaid
sequenceDiagram
    autonumber
    participant Input as Signal Provider (API / Scanner)
    participant DB as SQL Database
    participant Orchestrator as ExecutionLoop & DecisionPipeline
    participant Council as AI Council Debate
    participant Risk as RiskEngine & ExecutionGuard
    participant Exec as PaperExecutor / TradeEngine
    participant WS as WebSocket Room ("trades" & "notifications")

    Input->>DB: Post Raw Signal (Status: OPEN, approved: False)
    Orchestrator->>DB: Poll for OPEN Signals
    DB-->>Orchestrator: Return Signal List

    Orchestrator->>Council: Invoke AI Council (Market, Technical, Risk, Whale, News Agents)
    Council-->>Orchestrator: Debate & Consensus (Direction, Composite Score, Reasons)

    Orchestrator->>Orchestrator: Apply 5-Factor Scoring (Trend, Volume, BTC, MTF, Risk)
    Orchestrator->>Orchestrator: Calculate Confidence Score (0 - 100%)

    Orchestrator->>Risk: Assess Risk (Max open limit, drawdowns, volatility filters)
    Risk-->>Orchestrator: Return RiskDecision (PASS / REJECT)

    alt Risk Decision is PASS
        Orchestrator->>Exec: Route to TradeEngine
        Exec->>Exec: Calculate ATR-based TP/SL levels & Position Size
        Exec->>DB: Persist Trade & Update Signal Status to CLOSED
        Exec->>WS: Broadcast Trade Opened Payload
    else Risk Decision is REJECT
        Orchestrator->>DB: Update Signal Status to REJECTED & record RejectionReason
        Orchestrator->>WS: Broadcast Signal Rejected Event
    end

    loop Paper Executor Loop (Every 10s)
        Exec->>Exec: Monitor Live Price against TP/SL levels
        alt TP or SL Hit
            Exec->>DB: Close Trade (Status: TP_HIT / SL_HIT, record PnL)
            Exec->>WS: Broadcast Trade Closed Event
        end
    end
```

---

## 🏛️ System Core Modules & Boundary Mapping

| Subsystem Module | Boundary & Namespace | Primary Location | Key Collaborators |
|------------------|----------------------|------------------|-------------------|
| **API Gateway** | `api` | `api/main.py`, `api/routes/` | `auth/`, `monitoring/` |
| **Real-time Engine** | `api.websocket` | `api/websocket/` | `notifications/` |
| **Orchestrator** | `core` / `execution` | `execution/execution_loop.py` | `database.py`, `scoring/`, `risk/` |
| **AI Council** | `council` | `council/` | `services/ai/` |
| **Explanation Engine**| `decision` | `decision/` | `database.py`, `services/` |
| **Evidence & Trace** | `decision.evidence` | `decision/evidence/` | `database.py`, `services/` |
| **Market Intelligence**| `market` | `market/` | `exchange/` |
| **Trade Execution** | `execution` | `execution/trade_engine.py` | `database.py` |
| **Risk Guards** | `risk` / `scoring` | `risk/execution_guard.py` | `scoring/risk_engine.py` |
| **Portfolio & KPI** | `portfolio` / `perf` | `portfolio_engine.py`, `performance_engine.py` | `database.py` |
