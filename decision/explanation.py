"""ReasonBuilder, SignalExplanation, RiskExplanation — human-readable reasoning."""

from __future__ import annotations

import logging
from typing import Any, Optional

from decision.models import DecisionResult
from market.models import Asset
from scanner.models import Opportunity

logger = logging.getLogger(__name__)


_REASON_TEMPLATES = {
    "BULLISH_TREND_ALIGNED": "EMA20 above EMA50 above EMA200 — strong bullish trend alignment",
    "BEARISH_TREND_ALIGNED": "EMA20 below EMA50 below EMA200 — strong bearish trend alignment",
    "RSI_BULLISH": "RSI above 60 — bullish momentum",
    "RSI_BEARISH": "RSI below 40 — bearish momentum",
    "PRICE_BREAKOUT_HIGH": "Price broke above recent range with EMA confirmation",
    "PRICE_BREAKOUT_LOW": "Price broke below recent range with EMA confirmation",
    "HIGH_VOLUME_CONFIRMATION": "Volume 50% above average — strong confirmation",
    "OVERSOLD_REVERSAL": "Oversold conditions suggest potential reversal upward",
    "OVERBOUGHT_REVERSAL": "Overbought conditions suggest potential reversal downward",
    "HIGH_LIQUIDITY": "High liquidity — favorable for execution",
    "LOW_LIQUIDITY": "Low liquidity — execute with caution",
    "MOMENTUM_STRONG": "Strong momentum detected",
    "FEATURE_BULLISH": "Feature store confirms bullish conditions",
    "FEATURE_BEARISH": "Feature store confirms bearish conditions",
}

_WARNING_TEMPLATES = {
    "LOW_VOLUME_BREAKOUT": "Breakout on low volume — may be false signal",
    "TREND_REVERSAL_CONFLICT": "Trend and reversal signals conflict — wait for confirmation",
    "RSI_OVERBOUGHT_WITH_BULLISH": "RSI overbought while bullish — potential exhaustion",
    "EXTREME_GREED_CAUTION": "Extreme greed — elevated risk of reversal",
    "HIGH_FUNDING_LONG_PENALTY": "High funding rate for longs — expensive to hold",
    "EXTREME_VOLATILITY_RISK": "Extreme volatility — wide stops required",
}


class ReasonBuilder:
    """Build structured reasoning from signals, features, and intelligence."""

    def build(self, opportunity: Opportunity, asset: Optional[Asset] = None) -> list[str]:
        reasons: list[str] = []

        for signal in opportunity.signals:
            template = _REASON_TEMPLATES.get(signal)
            if template:
                reasons.append(template)

        if opportunity.probability_signals:
            for ps in opportunity.probability_signals:
                if ps == "STRONG_TREND_BOOST":
                    reasons.append("Strong trend increases probability of success")
                elif ps == "BTC_BULLISH_CONTEXT":
                    reasons.append("Bullish BTC context supports the trade")
                elif ps == "FEAR_BUYING_OPPORTUNITY":
                    reasons.append("Fear index suggests buying opportunity")

        if asset and asset.intelligence:
            fg = asset.intelligence.fear_greed
            if fg:
                value = fg.get("value", 50)
                label = fg.get("label", "NEUTRAL")
                reasons.append(f"Fear & Greed: {label} ({value})")

            liq = asset.intelligence.liquidity_context
            if liq:
                level = liq.get("level", "UNKNOWN")
                if level == "HIGH":
                    reasons.append("High liquidity ensures tight spreads")

        return reasons

    def build_warnings(self, opportunity: Opportunity) -> list[str]:
        warnings: list[str] = []
        for signal in opportunity.signals:
            template = _WARNING_TEMPLATES.get(signal)
            if template:
                warnings.append(template)

        for ps in opportunity.probability_signals:
            if ps == "EXTREME_GREED_CAUTION":
                warnings.append("Extreme greed — consider reducing position size")
            elif ps == "HIGH_FUNDING_LONG_PENALTY":
                warnings.append("High funding costs may erode profits")

        if opportunity.risk_signals:
            for rs in opportunity.risk_signals:
                if rs == "EXTREME_VOLATILITY_RISK":
                    warnings.append("Extreme volatility — use wider stops")
                elif rs == "LOW_LIQUIDITY_RISK":
                    warnings.append("Low liquidity — slippage may be significant")
                elif rs == "HIGH_ATR_RISK":
                    warnings.append("High ATR — position size should be reduced")

        return warnings


class SignalExplanation:
    """Provide human-readable explanation for signals."""

    def explain_signal(self, signal: str) -> str:
        return _REASON_TEMPLATES.get(signal, f"Signal: {signal}")

    def explain_signals(self, signals: list[str]) -> list[str]:
        return [self.explain_signal(s) for s in signals]


class RiskExplanation:
    """Explain risk factors in human-readable form."""

    def explain(self, risk_score: float, opportunity: Opportunity) -> str:
        if risk_score >= 0.7:
            level = "HIGH"
        elif risk_score >= 0.4:
            level = "MODERATE"
        else:
            level = "LOW"

        parts: list[str] = [f"Risk level: {level} ({risk_score:.2f})"]

        for rs in opportunity.risk_signals:
            if rs == "EXTREME_VOLATILITY_RISK":
                parts.append("Volatility is extreme")
            elif rs == "HIGH_VOLATILITY_RISK":
                parts.append("Volatility is elevated")
            elif rs == "HIGH_FEATURE_RISK":
                parts.append("Feature store indicates elevated risk")
            elif rs == "HIGH_ATR_RISK":
                parts.append("ATR is high — expect wider price swings")
            elif rs == "LOW_LIQUIDITY_RISK":
                parts.append("Liquidity is low — execution may be challenging")
            elif rs == "REVERSAL_RISK":
                parts.append("Reversal strategies carry inherent risk")
            elif rs == "LOW_VOLATILITY_BOOST":
                parts.append("Low volatility — favorable conditions")
            elif rs == "HIGH_LIQUIDITY_BOOST":
                parts.append("High liquidity — favorable execution conditions")

        return " | ".join(parts)
