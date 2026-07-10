from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class DailyAnalyticsDTO:
    date: str = ""
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    pnl: float = 0.0
    avg_pnl: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WeeklyAnalyticsDTO:
    week: str = ""
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    pnl: float = 0.0
    avg_pnl: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MonthlyAnalyticsDTO:
    month: str = ""
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    pnl: float = 0.0
    avg_pnl: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WinLossAnalyticsDTO:
    total_wins: int = 0
    total_losses: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0
    avg_holding_time_win: float = 0.0
    avg_holding_time_loss: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SymbolAnalyticsDTO:
    symbol: str = ""
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    profit_factor: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StrategyAnalyticsDTO:
    strategy_name: str = ""
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    overall_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskAnalyticsDTO:
    max_open_trades: int = 0
    current_open_trades: int = 0
    symbol_exposure: dict[str, float] = field(default_factory=dict)
    portfolio_exposure: float = 0.0
    max_portfolio_exposure: float = 0.0
    daily_loss: float = 0.0
    max_daily_loss: float = 0.0
    risk_score: float = 0.0
    rejection_rate: float = 0.0
    total_rejections: int = 0
    rejection_reasons: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DrawdownAnalyticsDTO:
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    current_drawdown: float = 0.0
    current_drawdown_pct: float = 0.0
    recovery_count: int = 0
    avg_recovery_time_hours: float = 0.0
    longest_drawdown_hours: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HeatmapDataDTO:
    symbol: str = ""
    metric: str = ""
    values: dict[str, float] = field(default_factory=dict)
    intensity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceTrendDTO:
    metric: str = ""
    daily_values: list[dict[str, Any]] = field(default_factory=list)
    weekly_values: list[dict[str, Any]] = field(default_factory=list)
    monthly_values: list[dict[str, Any]] = field(default_factory=list)
    trend_direction: str = ""
    change_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KPIDTO:
    name: str = ""
    value: float = 0.0
    previous_value: float = 0.0
    change_pct: float = 0.0
    unit: str = ""
    trend: str = ""
    status: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalyticsDTO:
    daily: list[DailyAnalyticsDTO] = field(default_factory=list)
    weekly: list[WeeklyAnalyticsDTO] = field(default_factory=list)
    monthly: list[MonthlyAnalyticsDTO] = field(default_factory=list)
    win_loss: Optional[WinLossAnalyticsDTO] = None
    by_symbol: list[SymbolAnalyticsDTO] = field(default_factory=list)
    by_strategy: list[StrategyAnalyticsDTO] = field(default_factory=list)
    risk: Optional[RiskAnalyticsDTO] = None
    drawdown: Optional[DrawdownAnalyticsDTO] = None
    heatmap: list[HeatmapDataDTO] = field(default_factory=list)
    trends: list[PerformanceTrendDTO] = field(default_factory=list)
    kpis: list[KPIDTO] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = {}
        for key in ("daily", "weekly", "monthly", "by_symbol", "by_strategy", "heatmap", "trends", "kpis"):
            items = getattr(self, key, [])
            d[key] = [i.to_dict() if hasattr(i, "to_dict") else asdict(i) for i in items]
        for key in ("win_loss", "risk", "drawdown"):
            val = getattr(self, key, None)
            d[key] = val.to_dict() if val else None
        return d
