# Sprint 14 — Performance Analytics Engine

## Objective
Build a standalone Performance Analytics Engine that evaluates trading strategy quality from the Trade database — independent from PortfolioEngine.

## Architecture

```
Trade(DB)
    ↓
PerformanceEngine.stats()  →  PerformanceStats
    ↓
    - Sharpe Ratio
    - Sortino Ratio
    - Profit Factor
    - Expectancy
    - Recovery Factor
    - Calmar Ratio
    - Average R Multiple
    - Average Holding Time
    - Consecutive Wins / Losses
    - Best / Worst Trade
```

Read-only, injectable `session_factory`, no coupling to any other engine.

## Metrics & Formulas

| # | Metric | Formula | Notes |
|---|--------|---------|-------|
| 1 | Sharpe Ratio | `(mean(R) − Rf) / σ(R)` | R = per-trade return (pnl/entry). Sentinel 999.99 when σ=0 and mean > Rf. |
| 2 | Sortino Ratio | `(mean(R) − Rf) / σ_down(R)` | σ_down = sqrt(mean(min(0,R)²)). Sentinel 999.99 when no downside. |
| 3 | Profit Factor | `Σwin / \|Σloss\|` | Same as PortfolioEngine. 999.99 when no losses. |
| 4 | Expectancy | `WR × avg_win − LR × \|avg_loss\|` | Expected PnL per trade in dollars. |
| 5 | Recovery Factor | `ΣPnL / max_dd_dollars` | Total return relative to max dollar drawdown. |
| 6 | Calmar Ratio | `(ΣPnL / equity) / max_dd_pct` | Return % divided by max drawdown %. |
| 7 | Avg R Multiple | `mean(pnl / \|entry − stop\|)` | Risk-normalized return per trade. |
| 8 | Avg Holding Time | `mean(closed_at − created_at)` | In hours. |
| 9 | Consecutive Wins | Longest streak of pnl > 0 | Sorted by closed_at. |
| 10 | Consecutive Losses | Longest streak of pnl < 0 | Sorted by closed_at. |
| 11 | Best Trade | `max(pnl)` | Highest single-trade PnL. |
| 12 | Worst Trade | `min(pnl)` | Lowest single-trade PnL. |

## Files Modified

### New: `performance_engine.py` (217 lines)
- `PerformanceStats` dataclass with all 12 fields
- `PerformanceEngine` class with `stats()` method
- Constructor accepts `session_factory`, `initial_equity`, `risk_free_rate`

### New: `tests/test_performance_engine.py` (183 lines)
9 test cases covering every metric.

## Tests

```
$ python -m pytest tests/ -v
========================= 34 passed in 4.11s =========================
```

- `test_empty_portfolio` — all metrics 0
- `test_all_winners` — Sharpe=2.0, Sortino=999.99, PF=999.99, 3 consecutive wins
- `test_all_losers` — Sharpe=−2.0, Sortino≈−0.93, PF=0.0, 3 consecutive losses
- `test_mixed_trades` — Sharpe≈0.55, PF=4.0, expectancy=$200
- `test_expectancy` — 2 wins @ $1000 + 2 losses @ $500 → expectancy=$250
- `test_r_multiple` — R multiples 2.0, −0.5, 1.0 → avg = 0.83
- `test_holding_time` — single trade at 24h → avg = 24.0h
- `test_consecutive_streaks` — pattern WWLLLW → max wins=2, max losses=3
- `test_recovery_and_calmar` — sequence +2000, +3000, −4000, +1000 → recovery=0.5, calmar≈0.75

## Git Diff

```
performance_engine.py           │ 217 lines (new)
tests/test_performance_engine.py│ 183 lines (new)
```

No existing files modified.

## Remaining Blockers

None.

## Next Recommendation

**Sprint 15 — Consolidated CLI dashboard**: Combine PortfolioEngine and PerformanceEngine into a single `python -m engine report` CLI command that prints both portfolio stats and performance analytics to stdout in a formatted table.
