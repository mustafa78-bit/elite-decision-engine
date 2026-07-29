# NEXUS Architecture Knowledge Base

This documentation was automatically generated during Sprint 15 to serve as a single authoritative engineering reference of the platform.

---

## 1. High-Level Architecture Map

The NEXUS platform uses a modular, multi-tier decision operating system design, organized cleanly into decoupled logical domains:

```
                          ┌───────────────────────────┐
                          │   Founder UI (HUD Deck)   │
                          └─────────────┬─────────────┘
                                        │ (HTTP / WS)
                          ┌─────────────▼─────────────┐
                          │    FastAPI Gateway API    │
                          └─────────────┬─────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             │                          │                          │
   ┌─────────▼─────────┐      ┌─────────▼─────────┐      ┌─────────▼─────────┐
   │  Market Service   │      │  Decision Engine  │      │ Telemetry Service │
   └─────────┬─────────┘      └─────────┬─────────┘      └─────────┬─────────┘
             │                          │                          │
   ┌─────────▼─────────┐      ┌─────────▼─────────┐                │
   │  Collector Layer  │      │  Execution Loop   │                │
   └───────────────────┘      └─────────┬─────────┘                │
                                        │                          │
                                        │ (SQLAlchemy ORM)         │
                               ┌────────▼────────┐                 │
                               │  PostgreSQL /   ◄─────────────────┘
                               │  SQLite Store   │
                               └─────────────────┘
```

---

## 2. Core Service Directory

| Domain Service | Class Name | Location | Primary Responsibility |
|----------------|------------|----------|------------------------|
| **Market Intelligence** | `MarketDataService` | `market/services/market_data.py` | Orchestrates raw OHLCV fetching and multi-dimensional indicators. |
| **Opportunity Scanner** | `OpportunityScanner` | `scanner/core.py` | Multi-strategy discovery engine evaluating trend, momentum, breakouts. |
| **Intelligence Enricher**| `IntelligenceService`| `market/intelligence/service.py` | Enrich assets with Fear & Greed, whale actions, and exchange flows. |
| **Decision Aggregator** | `DecisionAggregator` | `decision/aggregator.py` | Merges scanner signals with market data to output unified decisions. |
| **Explanation Engine**  | `ExplainService` | `explain/engine.py` | Builds human-readable justifications and risk warnings. |
| **Platform Monitoring**  | `HealthService` | `monitoring/health.py` | Performs liveness, connection pool latency, and runtime diagnostics. |
| **Product Telemetry**    | `TelemetryService` | `services/telemetry_service.py` | Persists and indexes user workflow focus times and outcomes. |

---

## 3. Database Schema Blueprint

The platform's storage consists of these structured relational models:

### 3.1 `signals` Table
- `id` (Integer, Primary Key)
- `symbol` (String) — e.g., `BTCUSDT`
- `side` (String) — `LONG` or `SHORT`
- `score` (Float) — Base signal strength
- `status` (String) — e.g., `OPEN`, `EXECUTED`, `REJECTED`
- `reason` (Text) — Rejection or validation rationale

### 3.2 `trades` Table
- `id` (Integer, Primary Key)
- `signal_id` (Integer) — Link to source signal
- `symbol` (String)
- `side` (String)
- `entry` (Float) — Execution entry price
- `stop` (Float) — Stop loss level
- `tp1`, `tp2` (Float) — Take profit levels
- `pnl` (Float) — Realized/unrealized profit or loss
- `status` (String) — e.g. `OPEN`, `CLOSED`, `TP_HIT`, `SL_HIT`

### 3.3 `journal_entries` Table
- `id` (Integer, Primary Key)
- `symbol` (String)
- `entry_price`, `exit_price` (Float)
- `score`, `confidence` (Float)
- `entry_reason`, `exit_reason`, `notes` (Text) — Founder logs
- `result` (String) — `WIN`, `LOSS`, or `PENDING`

### 3.4 `telemetry_events` Table
- `id` (Integer, Primary Key)
- `timestamp` (DateTime) — Time-series index
- `screen` (String) — e.g., `morning_brief`
- `action` (String) — e.g., `opened`, `executed`
- `duration` (Float) — Focus focus time in seconds
- `outcome` (String) — Success or selected options

---

## 4. REST Routing Layout

NEXUS exposes a clean, nested routing architecture:

- **`/auth`** — Authentication token generation and user registration.
- **`/paper`** — Paper trading order lifecycle, position logs, and trade details.
- **`/analytics`** — Deep time-series win/loss charts, heatmaps, and product analytics.
- **`/monitoring`** — Platform liveness probe, latency pings, and engineering telemetry.
- **`/telemetry`** — Front-end interaction tracking and unified event stream.
