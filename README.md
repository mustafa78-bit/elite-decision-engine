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

```bash
# Install
pip install -r requirements.txt

# Run
python app.py

# Tests
rm -f test_elite.db && python -m pytest tests/ -v
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
| `MAX_EXPOSURE_PER_SYMBOL` | `200000` | Max USD per symbol |
| `MAX_PORTFOLIO_EXPOSURE` | `500000` | Max portfolio USD |
| `MAX_DAILY_LOSS` | `10000` | Max daily loss USD |
| `MAX_POSITION_SIZE_USD` | `100000` | Max position size USD |
| `ACCOUNT_EQUITY` | `10000` | Account equity for sizing |
| `RISK_PER_TRADE_PERCENT` | `1.0` | Risk % per trade |
| `ATR_MULTIPLIER` | `1.5` | ATR multiplier for SL |
| `MIN_POSITION_QUANTITY` | `0.001` | Minimum position qty |

## Tests

34 tests across 6 test files:

```
tests/test_integration.py        — End-to-end pipeline (6 phases)
tests/test_risk_manager.py       — 5 risk rules
tests/test_position_sizing.py    — ATR-based sizing
tests/test_portfolio_engine.py   — 14 portfolio metrics
tests/test_performance_engine.py — 12 performance metrics
```

## Logging

Log files in `logs/`:

- `engine.log` — core engine, database, app
- `trade.log` — execution, scoring
- `error.log` — all ERROR+ messages

10 MB rotation, 5 backups per file.
