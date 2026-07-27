# ARCHITECTURE — Elite Decision Engine

> **Version**: 1.0.0-founder-alpha | **Status**: Release Candidate | **Last Updated**: July 2026

---

## 1. System Overview

Elite Decision Engine is an AI-powered paper trading and decision intelligence platform. It ingests market data, evaluates opportunities through a multi-stage decision pipeline, manages risk parameters, executes paper trades, and monitors performance, exposing REST/WS APIs to a high-density frontend dashboard.

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

1. **Layered Pipeline**: Single-responsibility steps: Pipeline → Loop → Engine → Executor.
2. **Dependency Injection**: Injectable dependencies/session-factories across all core engines for test isolation.
3. **Protocol-based Interfaces**: Interfaces utilize typed contracts for collectors, filters, scorers, and confidence calculators.
4. **Event-Driven Notifications**: Real-time trade events broadcast via a unified `NotificationDispatcher` to WebSockets and Telegram.
5. **Separation of Concerns**: Complete decoupling of Market Data, Scoring, Risk, and Notifications.

---

## 3. Core Flows

### 3.1 Market Data Flow
All market data flows through the **Market Intelligence Platform (MIP)** layer:
1. High-frequency feeds collect ticker and candle updates from external exchanges (e.g., Hyperliquid API) via `HyperliquidCollector`.
2. Raw data is cached in a thread-safe `CacheManager` with configurable per-key TTLs.
3. Decoupled sub-services enrich raw data:
   - `IndicatorService` / `IndicatorEngine`: Calculates EMAs, RSI, and ATR.
   - `FeatureStore`: Generates advanced predictive indicators.
   - `ContextService`: Aggregates contextual data (open interest, funding rates, news sentiment, liquidation heatmap, whale flows).
4. `MarketDataService` acts as the single unified entry point, consolidating these layers into fully enriched `Asset` models.

### 3.2 Decision Pipeline & Execution Flow
Open signals are evaluated and executed through a deterministic multi-stage workflow:

```
TradingSignal (DB)
  │
  ▼
DecisionPipeline.evaluate()
  │
  ├── 1. Fetch data from MarketDataService
  ├── 2. Verify BTC market health gate (BTCHealthFilter)
  ├── 3. Score across 5 components (EMA, RSI, ATR, Volatility, Volume)
  └── 4. Calculate final confidence & decision (ConfidenceEngine)
  │
  ▼  [If STRONGLY_APPROVED]
  │
RiskManager.evaluate_trade()
  │  Verify daily loss limits, maximum open trade counts, and exposure bounds
  ▼
PositionSizingEngine.calculate()
  │  Calculate exact position quantity, risk budget, and stop limits
  ▼
TradeEngine.create_trade()
  │  Calculate ATR-based Stop Loss & Take Profit limits, check duplicates, write to DB
  ▼
PaperExecutor (Monitoring Loop)
     Check open trades vs ticker price -> trigger TP/SL exits -> auto-close stale trades (>7d)
```

### 3.3 Risk Management Architecture
The **Risk Management** system implements strict multi-layer execution safeguards:
- **Pre-execution Gates**: `RiskManager` evaluates a `TradeCandidate` prior to entry. Rejects any order that would violate maximum open trades (default: 3), daily drawdowns, or asset concentration limits.
- **Position Sizing Engine**: Dynamically scales entry quantity according to stop-loss distance (R-multiple) and total account equity to enforce a deterministic risk-per-trade constraint.
- **Post-execution Protection**: Enforced programmatically by `PaperExecutor` monitoring, which guarantees that once a trade is live, stop-loss and take-profit targets are checked and executed with zero process-local delay.

---

## 4. AI & Decision Intelligence Core (NEXUS AI)

The artificial intelligence module is centralized under the **NEXUS AI** ecosystem (renamed from OLLO).

```
                 ┌────────────────────────────────┐
                 │          NEXUS AI              │
                 │   Premium operator assistant   │
                 └──────────────┬─────────────────┘
                                │
        ┌───────────────────────┼────────────────────────┐
        ▼                       ▼                        ▼
 ┌──────────────┐        ┌──────────────┐        ┌───────────────┐
 │  Collapsed   │        │   Expanded   │        │ Immersive     │
 │  Breathing   │        │ Side Console │        │ Workspace     │
 │   Orb Ring   │        │Drawer Panel  │        │ Conversation  │
 └──────────────┘        └──────────────┘        └───────────────┘
```

### 4.1 Workspace & Route Context-Awareness
NEXUS AI operates as a premium operator console utilizing three distinct states:
1. **Collapsed State**: A subtle breathing orb/ring in the bottom-right corner of the workspace.
2. **Expanded State**: A side console drawer panel auto-focusing on user queries.
3. **Conversation State**: An immersive full-screen dialog overlay.

The panel dynamically maps client-side routes to **Context Rooms** (e.g. Command Deck, Portfolio, Scanner). Upon transition, it invokes `greetNEXUS(room)` to retrieve room-specific metrics and suggest custom "Quick Intel Queries" (e.g., "Analyze my portfolio exposure").

### 4.2 Multi-Agent AI Council (Advisory Layer)
The platform integrates a multi-agent consensus system known as the **AI Council**:
- Enlists 6 domain-specific cognitive agents: Macro, Technical, Trend, Risk, News, and Whale Intelligence.
- Aggregates reports to compute consensus and Executive Summaries.
- **Latency Design**: Because LLM inference introduces significant execution delays, the **AI Council is integrated as an advisory layer**. It is strictly decoupled from the high-frequency live decision pipeline to guarantee zero execution latency.

---

## 5. Components Categorization

### 5.1 Active Production Core
These components are active, maintained, and covered by the 100% successful test suites:
- **`market/` Package**: The newer, high-performance Market Intelligence Platform (MIP) architecture. Includes `market.services.MarketDataService` as the single entry point.
- **`portfolio/` & `performance/` Packages**: Consolidated, modern modular engines used across all dashboard and analytics route endpoints.
- **`services/`**: Supporting coordinators, explanation services, widgets, and AI engines.
- **`scanner/`**: Scanner PRO modules, watchlist managers, and probability calculations.
- **`api/routes/`**: Standard endpoint routers (auth, trading, analytics, KPI, preferences, scanner, etc.).

### 5.2 Legacy Compatibility Components
These components are preserved to support older client versions, existing database schemas, or CLI scripts:
- **`api/routes/ollo.py`**: Kept as a backward-compatibility route redirecting to NEXUS services. Currently kept unregistered in the default production list to ensure clean endpoint namespaces, but fully functional when enabled.
- **`market_data/`**: Root directory containing traditional low-level event collectors (live websocket broadcast tasks, volatile engines, funding/OI collectors) which run side-by-side with MIP.

### 5.3 Deprecated Components
- **`portfolio_engine.py` (root)**: Deprecated in favor of the modular `portfolio.engine` package. Maintained strictly for legacy compatibility.
- **`performance_engine.py` (root)**: Deprecated in favor of the modular `performance.engine` package. Maintained strictly for legacy compatibility.

---

## 6. Service Ownership & Directories

| Module / Package | Description | Primary Classes / Service | Scope |
|------------------|-------------|---------------------------|-------|
| `market/` | Market Intelligence Platform (MIP) | `MarketDataService` | High-performance cache & data integration |
| `portfolio/` | Portfolio Management Engine | `PortfolioEngine` | Cash, position sizing, exposure DTOs |
| `performance/` | Performance Engine | `PerformanceEngine` | Sharpe, Sortino, Calmar, Expectancy ratios |
| `council/` | AI Council Multi-Agent System | `ConsensusEngine` | Advisory cognitive reports |
| `decision/` | Pipeline & Evidence System | `DecisionPipeline` | Core execution checks and indicators |
| `simulator/` | Standalone Isolated Simulator | `ExecutionSimulator` | Isolated paper-trading simulation |
| `api/` | FastAPI Routes and WebSocket Manager| `app`, `WebSocketManager` | Web API Layer |

---

*End of ARCHITECTURE.md*
