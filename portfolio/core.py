from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PortfolioSnapshot:
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
