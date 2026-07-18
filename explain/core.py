from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExplainInput:
    symbol: str = ""
    side: str = ""

    technical_score: float = 0.0
    whale_score: float = 0.0
    news_score: float = 0.0
    risk_score: float = 0.0
    trend_score: float = 0.0

    portfolio_total_equity: float = 0.0
    portfolio_unrealized_pnl: float = 0.0
    portfolio_realized_pnl: float = 0.0
    portfolio_exposure: float = 0.0
    portfolio_initial_capital: float = 0.0

    performance_sharpe: float = 0.0
    performance_sortino: float = 0.0
    performance_calmar: float = 0.0
    performance_profit_factor: float = 0.0
    performance_win_rate: float = 0.0
    performance_total_pnl: float = 0.0
    performance_max_drawdown: float = 0.0


@dataclass
class ExplainResult:
    decision: str = ""
    confidence: float = 0.0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    supporting_signals: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    summary: str = ""
