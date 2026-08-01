from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

WEIGHTS = {
    "score": 0.25,
    "confidence": 0.20,
    "historical_win_rate": 0.20,
    "trend_alignment": 0.15,
    "volatility_condition": 0.10,
    "regime_alignment": 0.10,
}


@dataclass
class RankedSignal:
    rank: int
    signal_id: int
    symbol: str
    side: str
    raw_score: float
    confidence: float
    historical_win_rate: float
    trend_alignment: float
    volatility_condition: float
    regime_alignment: float
    composite_score: float
    recommendation: str
    reasons: list[str] = field(default_factory=list)


class SignalRankingAI:
    """AI-driven signal ranking combining quality, confidence, and historical success."""

    def __init__(self, weights: Optional[dict[str, float]] = None) -> None:
        self.weights = weights or WEIGHTS

    def rank_signals(self, signals: list[dict[str, Any]]) -> list[RankedSignal]:
        """Rank a list of signal dicts by composite score."""
        ranked: list[RankedSignal] = []
        for i, s in enumerate(signals):
            rs = self._rank_single(s)
            ranked.append(rs)
        ranked.sort(key=lambda r: r.composite_score, reverse=True)
        for idx, r in enumerate(ranked):
            r.rank = idx + 1
        return ranked

    def _rank_single(self, signal: dict[str, Any]) -> RankedSignal:
        raw_score = float(signal.get("score", 0))
        confidence = float(signal.get("confidence", 0))
        hist_win_rate = float(signal.get("historical_win_rate", 0.5))
        trend_align = float(signal.get("trend_alignment", 0.5))
        vol_cond = float(signal.get("volatility_condition", 0.5))
        regime_align = float(signal.get("regime_alignment", 0.5))

        score_norm = min(raw_score / 100.0, 1.0)
        conf_norm = min(confidence / 100.0, 1.0)

        composite = (
            score_norm * self.weights["score"]
            + conf_norm * self.weights["confidence"]
            + hist_win_rate * self.weights["historical_win_rate"]
            + trend_align * self.weights["trend_alignment"]
            + vol_cond * self.weights["volatility_condition"]
            + regime_align * self.weights["regime_alignment"]
        )

        rec, reasons = self._recommendation(composite, raw_score, confidence)

        return RankedSignal(
            rank=0,
            signal_id=int(signal.get("id", 0)),
            symbol=str(signal.get("symbol", "")),
            side=str(signal.get("side", "")),
            raw_score=raw_score,
            confidence=confidence,
            historical_win_rate=round(hist_win_rate, 4),
            trend_alignment=round(trend_align, 4),
            volatility_condition=round(vol_cond, 4),
            regime_alignment=round(regime_align, 4),
            composite_score=round(composite, 4),
            recommendation=rec,
            reasons=reasons,
        )

    def _recommendation(self, composite: float, raw_score: float, confidence: float) -> tuple[str, list[str]]:
        reasons: list[str] = []
        if composite >= 0.8:
            rec = "STRONG_BUY"
            reasons.append("High composite score")
        elif composite >= 0.6:
            rec = "BUY"
            reasons.append("Moderate composite score")
        elif composite >= 0.4:
            rec = "WATCH"
            reasons.append("Below-average composite score")
        else:
            rec = "PASS"
            reasons.append("Low composite score")

        if raw_score >= 85:
            reasons.append("High raw score")
        if confidence >= 80:
            reasons.append("High confidence")
        if composite < 0.4:
            reasons.append("Multiple factors below threshold")

        return rec, reasons

    def get_trend_alignment(self, signal_side: str, market_trend: str) -> float:
        """Score how well a signal aligns with the market trend."""
        alignment: dict[str, dict[str, float]] = {
            "LONG": {"BULLISH": 1.0, "RECOVERING": 0.8, "NEUTRAL": 0.5, "WEAKENING": 0.3, "BEARISH": 0.1},
            "SHORT": {"BULLISH": 0.1, "RECOVERING": 0.2, "NEUTRAL": 0.5, "WEAKENING": 0.7, "BEARISH": 1.0},
        }
        return alignment.get(signal_side.upper(), {}).get(market_trend, 0.5)

    def get_volatility_condition(self, volatility_class: str) -> float:
        """Score how favorable volatility is for trading."""
        scores = {"LOW": 0.7, "NORMAL": 1.0, "HIGH": 0.5, "EXTREME": 0.1, "UNKNOWN": 0.5}
        return scores.get(volatility_class, 0.5)

    def get_regime_alignment(self, signal_side: str, regime: str) -> float:
        """Score how well a signal aligns with the detected regime."""
        alignment: dict[str, dict[str, float]] = {
            "LONG": {"TREND": 1.0, "RECOVERY": 0.8, "RANGE": 0.6, "DOWNTREND": 0.1, "DEAD": 0.0},
            "SHORT": {"TREND": 0.1, "RECOVERY": 0.2, "RANGE": 0.5, "DOWNTREND": 1.0, "DEAD": 0.0},
        }
        return alignment.get(signal_side.upper(), {}).get(regime, 0.5)
