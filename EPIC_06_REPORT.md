# Epic 6: Elite Terminal Backend — Report

## Objective
Create unified backend support for Scanner, Dashboard, Portfolio, Market Health, Open Trades, Trade Journal, Notifications, Market Overview, and Performance Summary via REST endpoints and websocket events.

## Changes

### New files (3 files)

| File | Purpose |
|------|---------|
| `services/terminal_service.py` | `TerminalService` — aggregates all platform data (market, portfolio, performance, trades, signals, opportunities, risk) into a single overview |
| `api/routes/terminal.py` | REST endpoints: `/terminal/overview`, `/terminal/market`, `/terminal/open-trades`, `/terminal/opportunities`, `/terminal/signals`, `/terminal/risk`, `/terminal/portfolio`, `/terminal/performance` |
| `tests/test_terminal.py` | 11 tests covering TerminalService + API imports |

### Modified files (2 files)

| File | Change |
|------|--------|
| `api/events.py` | Added `ScannerPayload` + `ScannerEvent` websocket types (`SCANNER_UPDATE`) |
| `api/main.py` | Registered `terminal_router`, added `/ws/scanner` websocket endpoint |

## Terminal API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/terminal/overview` | Unified platform overview (all sections) |
| GET | `/terminal/market` | Market health (BTC price, trend, session, funding, Fear & Greed, RSI) |
| GET | `/terminal/open-trades` | Currently open trades from DB |
| GET | `/terminal/opportunities` | Top scanner opportunities |
| GET | `/terminal/signals` | Recent trading signals |
| GET | `/terminal/risk` | Risk status (score, open trades, limits) |
| GET | `/terminal/portfolio` | Portfolio summary (PnL, win rate, drawdown) |
| GET | `/terminal/performance` | Performance metrics (Sharpe, profit factor, expectancy) |

### New Websocket

| Path | Room | Event |
|------|------|-------|
| `/ws/scanner` | `scanner` | `SCANNER_UPDATE` |

## Data Flow

```
TerminalService
  ├── MarketDataService        → market health
  ├── OpportunityScanner       → top opportunities
  ├── DB (Trade)               → open trades
  ├── DB (Signal)              → recent signals
  ├── PortfolioEngine          → portfolio summary
  ├── PerformanceEngine        → performance metrics
  └── RiskEngine               → risk status
```

## Test Results

**168/168 tests pass** (11 terminal + 23 decision + 20 scanner + 39 PRO + 75 MIP)

## Commit

`pending`
