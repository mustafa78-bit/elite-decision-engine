from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Optional


@dataclass
class PortfolioSummaryDTO:
    total_balance: float = 0.0
    open_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_pnl: float = 0.0
    total_trades: int = 0
    open_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    avg_trade_duration: Optional[str] = None
    best_trade_pnl: float = 0.0
    worst_trade_pnl: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PortfolioDistributionDTO:
    by_symbol: Optional[list[dict[str, Any]]] = None
    by_side: Optional[dict[str, int]] = None
    by_strategy: Optional[list[dict[str, Any]]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PortfolioPerformanceDTO:
    equity_curve: Optional[list[dict[str, Any]]] = None
    monthly_pnl: Optional[list[dict[str, Any]]] = None
    daily_pnl: Optional[list[dict[str, Any]]] = None
    drawdown_curve: Optional[list[dict[str, Any]]] = None
    rolling_sharpe: Optional[list[dict[str, Any]]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PortfolioRiskDTO:
    current_exposure: float = 0.0
    max_exposure: float = 0.0
    symbol_concentration: Optional[dict[str, float]] = None
    risk_per_trade: float = 0.0
    var_95: float = 0.0
    expected_downside: float = 0.0
    recovery_factor: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
