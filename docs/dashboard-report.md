# Dashboard Report — Elite Decision Engine

## DashboardService

The `DashboardService` (previously `DashboardAggregator`) provides a comprehensive, cached aggregation of all system state for the Elite Terminal dashboard.

## Features

| Feature | Method | Description |
|---------|--------|-------------|
| Portfolio summary | `get_dashboard()` | Total trades, win rate, PnL, largest win/loss |
| Intelligence summary | `get_dashboard()` | Unified score, per-module health/scores, contribution report |
| Risk summary | `_build_risk()` | Risk score, max drawdown, volatility, Sharpe ratio, at-risk trades |
| Monitoring summary | `get_dashboard()` | Evaluate calls, active modules, decisions today, uptime |
| Performance summary | `get_performance_summary()` | Avg PnL, win rate, best/worst trade |
| Market overview | `get_market_overview()` | Total signals, active modules, module health |
| Trade history | `get_trade_history(n)` | Recent trades with full details |
| Active positions | `get_active_positions()` | Currently open positions |
| Notifications | `add_notification()` / `get_dashboard()` | Recent notifications (capped at 20) |
| Cache stats | `get_cache_stats()` | Cache size and TTL |
| Diagnostics | `get_diagnostics()` | Call count, cache hits/misses, errors |

## Caching

- Default TTL: 30 seconds
- Cache invalidated on `add_notification()` or explicit `invalidate_cache()`
- Falls back to stale cache on error if available
- `force_refresh=True` skips cache

## Risk Calculation

Risk metrics are computed from trade history:
- **Risk score**: `(1 - win_rate) * 100`
- **Max drawdown**: Maximum negative cumulative PnL
- **Volatility**: Standard deviation of percentage returns
- **Sharpe ratio**: `(win_rate - loss_rate) / (avg_loss / (avg_win + epsilon))`

## Performance

- All operations are O(n) in trade count
- Cache hit serves in O(1)
- Memory: trade storage capped at 10,000 entries
