from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PerformanceReport:
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    expectancy: float = 0.0
    payoff_ratio: float = 0.0
    recovery_factor: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    average_holding_time_hours: float = 0.0
    trade_frequency_per_day: float = 0.0
