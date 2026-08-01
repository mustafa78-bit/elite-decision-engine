"""Enhanced liquidity context analysis — fetched from real order book or fallback to heuristic."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Optional

from market.intelligence.binance_client import fetch_binance_depth

logger = logging.getLogger(__name__)


class LiquidityContextAnalyzer:
    """Provide enhanced liquidity context beyond basic classification."""

    def analyze(
        self,
        symbol: str,
        volume_score: Optional[float] = None,
        liquidity: Optional[str] = None,
        atr: Optional[float] = None,
        price: float = 0.0,
    ) -> dict[str, Any]:
        try:
            depth_data = fetch_binance_depth(symbol)
            if depth_data is None:
                raise ValueError("No depth data returned from any Binance hosts")

            bids = depth_data.get("bids", [])
            asks = depth_data.get("asks", [])
            if not bids or not asks:
                raise ValueError("Empty bids/asks from Binance order book")

            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            mid_price = (best_bid + best_ask) / 2.0
            spread_pct = (best_ask - best_bid) / mid_price * 100

            lower_bound = mid_price * 0.99
            upper_bound = mid_price * 1.01

            total_bid_depth = sum(float(b[1]) * float(b[0]) for b in bids if float(b[0]) >= lower_bound)
            total_ask_depth = sum(float(a[1]) * float(a[0]) for a in asks if float(a[0]) <= upper_bound)
            total_depth_usd = total_bid_depth + total_ask_depth

            # Calculate a genuine liquidity score
            score = min(0.95, max(0.05, math.log10(1 + total_depth_usd) / 7.0))

            signals = ["API_SOURCE_BINANCE_ORDER_BOOK"]
            signals.append(f"DEPTH_USD_1PCT_{int(total_depth_usd)}")

            if spread_pct > 0.5:
                score *= 0.7
                signals.append("WIDE_SPREAD_WARNING")
            elif spread_pct > 0.1:
                score *= 0.9
                signals.append("MODERATE_SPREAD")
            else:
                signals.append("TIGHT_SPREAD")

            if atr and price > 0:
                atr_pct = atr / price * 100
                if atr_pct > 5:
                    score *= 0.7
                    signals.append("HIGH_SPREAD_WARNING")
                elif atr_pct > 2:
                    score *= 0.9
                    signals.append("MODERATE_SPREAD")

            score = round(max(0.0, min(1.0, score)), 4)

            if score >= 0.7:
                level = "HIGH"
            elif score >= 0.4:
                level = "MEDIUM"
            else:
                level = "LOW"

            return {
                "symbol": symbol,
                "score": score,
                "level": level,
                "signals": signals,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.warning("Binance order book request failed, falling back to heuristic: %s", e)
            return self._analyze_heuristic(symbol, volume_score, liquidity, atr, price)

    def _analyze_heuristic(
        self,
        symbol: str,
        volume_score: Optional[float] = None,
        liquidity: Optional[str] = None,
        atr: Optional[float] = None,
        price: float = 0.0,
    ) -> dict[str, Any]:
        liquidity_score = 0.5
        signals: list[str] = []

        if liquidity == "HIGH":
            liquidity_score = 0.8
            signals.append("HIGH_LIQUIDITY")
        elif liquidity == "MEDIUM":
            liquidity_score = 0.5
            signals.append("MEDIUM_LIQUIDITY")
        elif liquidity == "LOW":
            liquidity_score = 0.2
            signals.append("LOW_LIQUIDITY_WARNING")

        if volume_score is not None:
            liquidity_score = (liquidity_score + volume_score) / 2
            if volume_score > 0.8:
                signals.append("STRONG_VOLUME_DEPTH")
            elif volume_score < 0.3:
                signals.append("WEAK_VOLUME_WARNING")

        if atr and price > 0:
            atr_pct = atr / price * 100
            if atr_pct > 5:
                liquidity_score *= 0.7
                signals.append("HIGH_SPREAD_WARNING")
            elif atr_pct > 2:
                liquidity_score *= 0.9
                signals.append("MODERATE_SPREAD")

        liquidity_score = round(max(0.0, min(1.0, liquidity_score)), 4)

        if liquidity_score >= 0.7:
            level = "HIGH"
        elif liquidity_score >= 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "symbol": symbol,
            "score": liquidity_score,
            "level": level,
            "signals": signals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
