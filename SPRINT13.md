# Sprint 13 — Portfolio & Performance Engine

## Objective
Build a standalone Portfolio & Performance Engine that reads from the Trade database and calculates 14 metrics including drawdown, profit factor, and equity curve.

## Architecture

```
Trade(DB)
    ↓
PortfolioEngine.stats()  →  PortfolioStats
    ↓
session_factory injected (same pattern as PaperExecutor, RiskManager)
```

The engine is a pure reader — no writes, no side effects, no business logic inside TradeEngine. It can be called by any component (CLI, dashboard, scheduler) without modifying the execution pipeline.

## Metrics

| # | Metric | Definition | Source |
|---|--------|-----------|--------|
| 1 | Total Trades | COUNT all rows | `Trade` table |
| 2 | Open Trades | COUNT WHERE status = 'OPEN' | `status` column |
| 3 | Closed Trades | COUNT WHERE status IN (TP_HIT, SL_HIT, CLOSED) | `status` column |
| 4 | Winning Trades | COUNT WHERE pnl > 0 (closed only) | `pnl` column |
| 5 | Losing Trades | COUNT WHERE pnl < 0 (closed only) | `pnl` column |
| 6 | Win Rate | wins / (wins + losses) × 100 | derived |
| 7 | Total PnL | SUM(pnl) for all closed trades | `pnl` column |
| 8 | Daily PnL | SUM(pnl) for trades closed today (UTC) | `pnl` + `closed_at` |
| 9 | Average Win | AVG(pnl) WHERE pnl > 0 | derived |
| 10 | Average Loss | AVG(pnl) WHERE pnl < 0 | derived |
| 11 | Profit Factor | gross_profit / ABS(gross_loss) | derived |
| 12 | Max Drawdown | max peak-to-trough decline from equity curve | derived |
| 13 | Current Open Exposure | SUM(entry) WHERE status = 'OPEN' | `entry` column |
| 14 | Equity Curve | `[initial, initial+∑pnl₁, initial+∑pnl₂, …]` | derived |

### Edge cases
- **Empty portfolio**: All metrics 0, equity curve = `[initial_equity]`
- **Only winners**: win_rate = 100%, profit_factor = 999.99 (sentinel for infinite)
- **Only losers**: win_rate = 0%, profit_factor = 0.0
- **No closed trades**: win_rate, total_pnl, daily_pnl all 0; equity curve = `[initial_equity]`

## Files Modified

### New: `portfolio_engine.py` (134 lines)

- `PortfolioStats` dataclass with all 14 fields
- `PortfolioEngine` class with `stats()` method
- Constructor accepts `session_factory` (default `get_session`) and `initial_equity` (default `ACCOUNT_EQUITY`)

### New: `tests/test_portfolio_engine.py` (137 lines)

8 test cases across all metrics.

## Tests

```
$ python -m pytest tests/ -q
.................................
25 passed in 1.98s
```

- `test_empty_portfolio` — all zeros, equity_curve = [10000]
- `test_only_wins` — 3 winning trades, win_rate=100%, profit_factor=999.99
- `test_only_losses` — 3 losing trades, win_rate=0%, profit_factor=0.0
- `test_mixed_wins_and_losses` — 2 wins + 1 loss, win_rate=66.67%, PF=5.0
- `test_drawdown` — sequence +500, +1000, -800, -200, max_dd ≈ 8.7%
- `test_equity_curve` — verifies `[10000, 10500, 11500, 10700]`
- `test_daily_pnl` — only today's 2 trades count (yesterday's $300 excluded)
- `test_open_trades_exposure` — 2 open trades = $80K exposure

## Git Diff

```
portfolio_engine.py              │ 134 lines (new)
tests/test_portfolio_engine.py   │ 137 lines (new)
```

No existing files modified.

## Remaining Blockers

None.

## Next Recommendation

**Sprint 14 — API endpoint for portfolio stats**: Expose `PortfolioEngine.stats()` over a REST endpoint (FastAPI) or CLI command, so portfolio performance can be queried without direct DB access.
