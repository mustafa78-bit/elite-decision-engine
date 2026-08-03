from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PortfolioSnapshot:
    """A point-in-time snapshot of portfolio metrics.

    Note on trade counts:
    - closed_trades tracks the count of all terminated Trades.
    - closed_trades_with_pnl tracks the subset of terminated Trades that have
      matching PaperTrade records (providing quantity/pnl data needed for real
      dollar calculations).
    - win_rate, profit_factor, and realized_pnl are computed over this smaller,
      accurate subset of closed trades where actual dollar PnL data is known.
    """
    total_equity: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    exposure: float = 0.0
    long_exposure: float = 0.0
    short_exposure: float = 0.0
    position_count: int = 0
    cash: float = 0.0
    total_trades: int = 0
    open_trades: int = 0
    closed_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    equity_curve: list[float] = field(default_factory=list)
    initial_capital: float = 0.0
    closed_trades_with_pnl: int = 0
