"""Whale activity tracking — computed from real market data."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timezone
from typing import Any, Optional

import requests

from market_data.funding.collector import FundingCollector
from market_data.open_interest.collector import OpenInterestCollector

logger = logging.getLogger(__name__)

BINANCE_HOSTS = ["https://api.binance.com", "https://api.binance.us"]


class WhaleService:
    """Detect whale activity signals from market data."""

    def __init__(
        self,
        funding_collector: FundingCollector | None = None,
        oi_collector: OpenInterestCollector | None = None,
    ) -> None:
        self.funding_collector = funding_collector or FundingCollector()
        self.oi_collector = oi_collector or OpenInterestCollector()

    def _map_symbol(self, symbol: str) -> str:
        """Map asset symbol to Binance USDT trading pair."""
        clean = symbol.upper().replace("/", "").replace("-", "")
        if clean.endswith("USDT") or clean.endswith("USD"):
            return clean
        return f"{clean}USDT"

    def _binance_request(self, path: str, params: dict[str, Any]) -> Any | None:
        """Try querying Binance hosts sequentially to avoid geographic restriction 451 errors."""
        for host in BINANCE_HOSTS:
            url = f"{host}{path}"
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 451:
                    logger.debug("Binance host %s returned 451 (geoblocked), trying next...", host)
                else:
                    logger.debug("Binance host %s returned status %s: %s", host, response.status_code, response.text)
            except Exception as e:
                logger.debug("Failed requesting Binance host %s: %s", host, e)
        return None

    def detect(
        self,
        symbol: str,
        volume_score: float | None = None,
        volatility_score: float | None = None,
        price: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Detect whale activity signals from real market data."""
        signals: list[dict[str, Any]] = []
        real_data_success = False

        try:
            binance_pair = self._map_symbol(symbol)

            # 1. Fetch recent trades to detect unusually large single trades
            trades_data = self._binance_request("/api/v3/trades", {"symbol": binance_pair, "limit": 100})
            if trades_data and isinstance(trades_data, list):
                usdt_sizes: list[float] = []
                for t in trades_data:
                    try:
                        qty = float(t.get("qty", 0))
                        p = float(t.get("price", 0))
                        usdt_sizes.append(qty * p)
                    except (ValueError, TypeError):
                        continue

                if usdt_sizes:
                    avg_size = sum(usdt_sizes) / len(usdt_sizes)
                    # We look for single trades that are at least 5 times the average trade size in the sample,
                    # and also exceed 20,000 USDT to avoid noise in low volume assets.
                    threshold = max(avg_size * 5.0, 20000.0)

                    large_trades_count = 0
                    max_large_trade = 0.0
                    for size in usdt_sizes:
                        if size >= threshold:
                            large_trades_count += 1
                            if size > max_large_trade:
                                max_large_trade = size

                    if large_trades_count > 0:
                        real_data_success = True
                        confidence = min(0.5 + (large_trades_count * 0.05), 0.99)
                        severity = "high" if max_large_trade > 100000.0 else "medium"
                        signals.append({
                            "type": "WHALE_TRADE",
                            "symbol": symbol,
                            "severity": severity,
                            "description": f"Detected {large_trades_count} unusually large single trade(s) with max size {max_large_trade:,.2f} USDT",
                            "confidence": round(confidence, 2),
                            "timestamp": datetime.now(UTC).isoformat(),
                        })

            # 2. Fetch order book depth to calculate bid/ask volume imbalance
            depth_data = self._binance_request("/api/v3/depth", {"symbol": binance_pair, "limit": 100})
            if depth_data and isinstance(depth_data, dict):
                bids = depth_data.get("bids", [])
                asks = depth_data.get("asks", [])

                bid_vol = 0.0
                ask_vol = 0.0
                for b in bids[:50]:  # Look at the top 50 depth levels
                    try:
                        bid_vol += float(b[0]) * float(b[1])
                    except (ValueError, TypeError, IndexError):
                        continue
                for a in asks[:50]:
                    try:
                        ask_vol += float(a[0]) * float(a[1])
                    except (ValueError, TypeError, IndexError):
                        continue

                total_depth = bid_vol + ask_vol
                if total_depth > 0:
                    imbalance = (bid_vol - ask_vol) / total_depth
                    # If imbalance is extreme, it suggests whale wall presence
                    if abs(imbalance) >= 0.3:
                        real_data_success = True
                        wall_type = "Support" if imbalance > 0 else "Resistance"
                        severity = "high" if abs(imbalance) >= 0.5 else "medium"
                        signals.append({
                            "type": "WHALE_WALL",
                            "symbol": symbol,
                            "wall_type": wall_type,
                            "severity": severity,
                            "description": f"Strong whale {wall_type} wall detected (order book volume imbalance: {imbalance*100:+.1f}%)",
                            "confidence": round(abs(imbalance), 2),
                            "timestamp": datetime.now(UTC).isoformat(),
                        })

            # 3. Fetch funding & open interest from Hyperliquid (as extra signals if available)
            clean_coin = symbol.upper().replace("USDT", "").replace("USD", "")

            # Fetch funding history
            try:
                funding_history = self.funding_collector.fetch_funding_history(clean_coin, limit=5)
                if funding_history and not funding_history.empty:
                    latest_rate = funding_history.rates[0].rate
                    # Check if funding rate is unusually high or low (e.g. absolute > 0.05% per 8h)
                    if abs(latest_rate) >= 0.0005:
                        real_data_success = True
                        direction = "premium" if latest_rate > 0 else "discount"
                        signals.append({
                            "type": "EXTREME_FUNDING",
                            "symbol": symbol,
                            "direction": direction,
                            "severity": "high" if abs(latest_rate) >= 0.001 else "medium",
                            "description": f"Extreme funding rate detected ({latest_rate*100:.4f}% per interval), market in extreme {direction}",
                            "confidence": min(abs(latest_rate) * 1000.0, 0.95),
                            "timestamp": datetime.now(UTC).isoformat(),
                        })
            except Exception as e:
                logger.debug("Hyperliquid funding check bypassed for whale detection: %s", e)

            # Fetch open interest trend
            try:
                oi_trend = self.oi_collector.fetch_with_trend(clean_coin, limit=24)
                if oi_trend and oi_trend.get("value", 0) > 0:
                    trend = oi_trend.get("trend", "unknown").upper()
                    strength = oi_trend.get("strength", 0.0)
                    if trend in ("INCREASING", "SHARP_RISE") or strength > 0.5:
                        real_data_success = True
                        signals.append({
                            "type": "WHALE_MOVE",
                            "symbol": symbol,
                            "severity": "high" if strength >= 0.8 else "medium",
                            "description": f"Whale-driven open interest buildup detected (trend: {trend}, strength: {strength:.2f})",
                            "confidence": round(strength, 2),
                            "timestamp": datetime.now(UTC).isoformat(),
                        })
            except Exception as e:
                logger.debug("Hyperliquid open interest check bypassed for whale detection: %s", e)

        except Exception as e:
            logger.warning("Real whale activity detection failed for %s: %s", symbol, e)

        # Fallback to volume/volatility score heuristics if real data calls failed or returned nothing
        if not real_data_success:
            logger.debug("Real-data whale detection not successful or yielded no signals; falling back to heuristics")
            if volume_score is not None and volume_score > 0.9:
                signals.append({
                    "type": "HIGH_VOLUME",
                    "symbol": symbol,
                    "severity": "high" if volume_score > 0.95 else "medium",
                    "description": "Unusually high volume detected (heuristic fallback)",
                    "confidence": round(volume_score, 2),
                    "timestamp": datetime.now(UTC).isoformat(),
                })

            if volume_score and volatility_score:
                combined = volume_score * volatility_score
                if combined > 0.7:
                    signals.append({
                        "type": "WHALE_MOVE",
                        "symbol": symbol,
                        "severity": "high" if combined > 0.85 else "medium",
                        "description": "Potential whale accumulation/distribution (heuristic fallback)",
                        "confidence": round(combined, 2),
                        "timestamp": datetime.now(UTC).isoformat(),
                    })

        return signals
