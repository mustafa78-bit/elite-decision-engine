# Elite Decision Engine

Automated paper trading decision engine and AI coordination platform for cryptocurrency markets (Hyperliquid).

## Key Features

- **AI Agent Framework** — Multi-agent system leveraging specialized models (Technical, Trend, News, Whale, Risk, Macro) to produce structured intelligence.
- **Consensus & Conflict Engine** — Resolves differences between agents and constructs single high-confidence trading decisions.
- **Unified Workspaces** — React-based workspace cockpit matching existing Product Bibles.
- **Robust Execution Loop** — Fully-monitored paper-trading system validating risk parameters, exposure limits, and tracking real-time slippage/fees.

## Architecture

```
                    ┌──────────────┐
                    │  Trading     │
                    │  Signal      │
                    │  (DB: OPEN)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Decision    │
                    │  Engine      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Decision    │
                    │  Pipeline    │
                    │  (filter +   │
                    │   score +    │
                    │   conf)      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Risk        │
                    │  (exposure,  │
                    │   drawdown)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Trade       │
                    │  (DB: OPEN)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Paper       │
                    │  Executor    │
                    │  (monitor    │
                    │   TP/SL)     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Trade       │
                    │  (DB: CLOSED)│
                    └──────────────┘
```

## Quick Start

### Backend Installation

Ensure you have Python >= 3.13 and Poetry installed:

```bash
# Install dependencies
poetry install

# Run backend api server
poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Frontend Installation

Ensure you have Node.js and npm installed:

```bash
# Install dependencies
npm --prefix frontend install

# Run frontend development server
npm --prefix frontend run dev
```

## Testing & Verifications

We utilize a comprehensive verification pipeline for quality assurance:

```bash
# Run pytest backend suite
poetry run pytest

# Run vitest frontend suite
npm --prefix frontend test -- --run

# Run full compiler and test pipeline via custom tool
python3 /home/jules/self_created_tools/verify_all.py
```

## Configuration

Set via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///elite.db` | Production database |
| `TEST_DATABASE_URL` | `sqlite:///test_elite.db` | Test database |
| `CHECK_INTERVAL` | `10` | Poll interval (seconds) |
| `MIN_SCORE` | `85` | Minimum trading score |
| `MAX_OPEN_TRADES` | `3` | Max concurrent trades |
| `ACCOUNT_EQUITY` | `10000` | Account equity for sizing |
| `RISK_PER_TRADE_PERCENT` | `1.0` | Risk % per trade |
| `ATR_MULTIPLIER` | `1.5` | ATR multiplier for SL |
