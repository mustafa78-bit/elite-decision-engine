from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class StrategyScore:
    name: str
    win_rate: float = 0.0
    total_trades: int = 0
    total_pnl: float = 0.0
    avg_confidence: float = 0.0
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    overall_score: float = 0.0


class StrategyScorer:
    """Score and compare strategy performance."""

    def score(
        self,
        win_rate: float,
        total_pnl: float,
        avg_confidence: float,
        sharpe: float,
        max_drawdown: float,
        total_trades: int = 1,
    ) -> float:
        """Compute a composite score for a strategy.

        Weighted combination of:
        - win_rate (30%)
        - total_pnl normalized (20%)
        - avg_confidence (20%)
        - sharpe ratio (20%)
        - drawdown penalty (10%)
        """
        if total_trades == 0:
            return 0.0

        wr_score = min(win_rate / 100.0, 1.0) * 0.30

        pnl_norm = min(max(total_pnl / 10000, -1.0), 1.0)
        pnl_score = ((pnl_norm + 1) / 2) * 0.20

        conf_score = min(avg_confidence / 100.0, 1.0) * 0.20

        sharpe_norm = min(max(sharpe / 3.0, 0.0), 1.0)
        sharpe_score = sharpe_norm * 0.20

        dd_penalty = min(max_drawdown / 5000, 1.0) * 0.10
        dd_score = (1.0 - dd_penalty) * 0.10

        return round(wr_score + pnl_score + conf_score + sharpe_score + dd_score, 4)

    def compare(self, scores: list[StrategyScore]) -> list[StrategyScore]:
        """Sort strategies by overall_score descending."""
        for s in scores:
            s.overall_score = self.score(
                win_rate=s.win_rate,
                total_pnl=s.total_pnl,
                avg_confidence=s.avg_confidence,
                sharpe=s.sharpe,
                max_drawdown=s.max_drawdown,
                total_trades=s.total_trades,
            )
        return sorted(scores, key=lambda x: x.overall_score, reverse=True)
