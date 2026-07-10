from __future__ import annotations

import logging
from typing import Any

from scanner.models import Opportunity, ScanResult

logger = logging.getLogger(__name__)

_WEIGHTS = {
    "trend": 0.25,
    "momentum": 0.25,
    "breakout": 0.20,
    "reversal": 0.15,
    "liquidity": 0.15,
}


class OpportunityRanker:
    """Combine strategy scores into ranked opportunities."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or _WEIGHTS

    def rank(self, results: list[ScanResult]) -> list[Opportunity]:
        opportunities: list[Opportunity] = []
        for r in results:
            composite = (
                r.trend_score * self.weights["trend"]
                + r.momentum_score * self.weights["momentum"]
                + r.breakout_score * self.weights["breakout"]
                + r.reversal_score * self.weights["reversal"]
                + r.liquidity_score * self.weights["liquidity"]
            )
            r.composite_score = round(composite, 4)
            if composite <= 0:
                continue

            side = "LONG" if composite > 0 else "SHORT"
            opp = Opportunity(
                symbol=r.symbol,
                side=side,
                strategy=self._best_strategy(r),
                score=composite,
                confidence=min(composite * 100, 99.0),
                features=r.features,
                signals=r.signals,
            )
            opportunities.append(opp)

        opportunities.sort(key=lambda o: o.score, reverse=True)
        for i, opp in enumerate(opportunities):
            opp.rank = i + 1
        return opportunities

    def top(self, results: list[ScanResult], n: int = 5) -> list[Opportunity]:
        return self.rank(results)[:n]

    @staticmethod
    def _best_strategy(r: ScanResult) -> str:
        scores = {
            "trend": r.trend_score,
            "momentum": r.momentum_score,
            "breakout": r.breakout_score,
            "reversal": r.reversal_score,
            "liquidity": r.liquidity_score,
        }
        return max(scores, key=scores.get)
