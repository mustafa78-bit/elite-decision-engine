# Elite Decision Engine

Automated paper trading engine for cryptocurrency markets (Hyperliquid).

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
                    │  Manager     │
                    │  (5 rules)   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Position    │
                    │  Sizing      │
                    │  (ATR-based) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Trade       │
                    │  Engine      │
                    │  (TP/SL)     │
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

### Supporting Modules

- **PortfolioEngine** — 14 metrics (PnL, win rate, drawdown, etc.)
- **PerformanceEngine** — 12 metrics (Sharpe, Sortino, profit factor, etc.)
- **StartupValidator** — env vars, DB connectivity, config sanity
- **LoggingConfig** — rotating file handlers (engine.log, trade.log, error.log)

## Quick Start

Refer to the [Developer Onboarding Guide](docs/DEVELOPER_ONBOARDING_GUIDE.md) to get fully set up in under 60 minutes.

### Standard Setup

```bash
# Set Python global version
pyenv global 3.13.2

# Install dependencies using poetry
poetry env use 3.13.2
poetry install --no-root

# Run the seeding script
poetry run python seed_data.py

# Start the development API server
poetry run uvicorn api.main:app --reload --port 8000
```

### Running Tests

```bash
poetry run pytest
```

---

## Guidelines & Contributing

Please consult [CONTRIBUTING.md](CONTRIBUTING.md) for coding conventions, branching guidelines, and development workflows. See the latest test status in [VALIDATION_REPORT.md](VALIDATION_REPORT.md).

## Configuration

Set via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///elite.db` | Production database |
| `TEST_DATABASE_URL` | `sqlite:///test_elite.db` | Test database |
| `CHECK_INTERVAL` | `10` | Poll interval (seconds) |
| `MIN_SCORE` | `85` | Minimum trading score |
| `MAX_OPEN_TRADES` | `3` | Max concurrent trades |
| `MAX_EXPOSURE_PER_SYMBOL` | `200000` | Max USD per symbol |
| `MAX_PORTFOLIO_EXPOSURE` | `500000` | Max portfolio USD |
| `MAX_DAILY_LOSS` | `10000` | Max daily loss USD |
| `MAX_POSITION_SIZE_USD` | `100000` | Max position size USD |
| `ACCOUNT_EQUITY` | `10000` | Account equity for sizing |
| `RISK_PER_TRADE_PERCENT` | `1.0` | Risk % per trade |
| `ATR_MULTIPLIER` | `1.5` | ATR multiplier for SL |
| `MIN_POSITION_QUANTITY` | `0.001` | Minimum position qty |

## Tests

Over 1320+ unit and integration tests validate the complete end-to-end system reliability with 100% success rates.

## Logging

Log files in `logs/`:

- `engine.log` — core engine, database, app
- `trade.log` — execution, scoring
- `error.log` — all ERROR+ messages

10 MB rotation, 5 backups per file.
