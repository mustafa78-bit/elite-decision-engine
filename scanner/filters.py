"""MarketFilter and FalseSignalFilter — filter low-quality opportunities."""

from __future__ import annotations

import logging
from typing import Any, Optional

from scanner.models import ScanResult

logger = logging.getLogger(__name__)


class MarketFilter:
    """Filter opportunities based on macro market conditions."""

    def should_filter(
        self,
        result: ScanResult,
        btc_trend: Optional[str] = None,
        market_session: Optional[str] = None,
        fear_greed_label: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        trend = result.features.get("trend", "NEUTRAL")

        if btc_trend == "BEARISH" and trend in ("BULLISH", "MILD_BULLISH"):
            return True, "BTC_BEARISH_CONTRADICTS_BULLISH_TREND"

        if fear_greed_label in ("EXTREME_GREED",) and trend == "BULLISH":
            if result.momentum_score > 0.5 and result.reversal_score > 0.3:
                return True, "EXTREME_GREED_WITH_REVERSAL_SIGNAL"

        if fear_greed_label in ("EXTREME_FEAR",) and trend == "BEARISH":
            if result.reversal_score > 0.5:
                return True, "EXTREME_FEAR_PANIC_SELLING"

        if market_session == "CLOSED":
            return True, "MARKET_CLOSED"

        return False, None


class FalseSignalFilter:
    """Detect and suppress common false signal patterns."""

    LOW_VOLUME_BREAKOUT_THRESHOLD = 0.3

    def should_filter(
        self,
        result: ScanResult,
        volume_score: Optional[float] = None,
    ) -> tuple[bool, Optional[str]]:
        if result.breakout_score > 0.3:
            vol = volume_score or result.features.get("volume_score")
            if vol is not None and vol < self.LOW_VOLUME_BREAKOUT_THRESHOLD:
                return True, "LOW_VOLUME_BREAKOUT"

        if result.trend_score > 0.3 and result.reversal_score > 0.4:
            return True, "TREND_REVERSAL_CONFLICT"

        if result.signals.count("RSI_OVERBOUGHT") > 0 and result.signals.count("RSI_BULLISH") > 0:
            return True, "RSI_OVERBOUGHT_WITH_BULLISH"

        if result.signals.count("RSI_OVERSOLD") > 0 and result.signals.count("RSI_BEARISH") > 0:
            return True, "RSI_OVERSOLD_WITH_BEARISH"

        return False, None
