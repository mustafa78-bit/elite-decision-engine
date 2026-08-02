"""Fear & Greed Index — fetched from real API or computed as fallback."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timezone
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class FearGreedService:
    """Compute Fear & Greed index from available market data."""

    def compute(
        self,
        rsi: float | None = None,
        btc_trend: str | None = None,
        volatility_score: float | None = None,
        funding_rate: float | None = None,
    ) -> dict[str, Any]:
        try:
            resp = requests.get("https://api.alternative.me/fng/", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if "data" in data and len(data["data"]) > 0:
                item = data["data"][0]
                val = int(item["value"])
                classification = item["value_classification"]
                # Convert "Extreme Fear" -> "EXTREME_FEAR", etc.
                label = classification.upper().replace(" ", "_")

                # Check for label correctness. If not matching expectations, standard maps can be used.
                valid_labels = {"EXTREME_FEAR", "FEAR", "NEUTRAL", "GREED", "EXTREME_GREED"}
                if label not in valid_labels:
                    if "EXTREME" in label and "FEAR" in label:
                        label = "EXTREME_FEAR"
                    elif "FEAR" in label:
                        label = "FEAR"
                    elif "EXTREME" in label and "GREED" in label:
                        label = "EXTREME_GREED"
                    elif "GREED" in label:
                        label = "GREED"
                    else:
                        label = "NEUTRAL"

                confidence = round(1.0 - abs(val - 50) / 100, 2)

                # Extract api's unix timestamp and format as ISO
                try:
                    dt = datetime.fromtimestamp(int(item["timestamp"]), tz=UTC)
                    timestamp_iso = dt.isoformat()
                except Exception:
                    timestamp_iso = datetime.now(UTC).isoformat()

                return {
                    "value": val,
                    "label": label,
                    "signals": ["API_SOURCE_ALTERNATIVE_ME"],
                    "confidence": confidence,
                    "timestamp": timestamp_iso,
                }
            else:
                raise ValueError("Unexpected API response structure (missing data or empty list)")
        except Exception as e:
            logger.warning("FearGreed API request failed, falling back to heuristic: %s", e)
            return self._compute_heuristic(rsi, btc_trend, volatility_score, funding_rate)

    def _compute_heuristic(
        self,
        rsi: float | None = None,
        btc_trend: str | None = None,
        volatility_score: float | None = None,
        funding_rate: float | None = None,
    ) -> dict[str, Any]:
        score = 50.0
        signals: list[str] = []

        if rsi is not None:
            if rsi < 30:
                score -= 20
                signals.append("OVERSOLD_RSI")
            elif rsi < 40:
                score -= 10
                signals.append("LOW_RSI")
            elif rsi > 70:
                score += 20
                signals.append("OVERBOUGHT_RSI")
            elif rsi > 60:
                score += 10
                signals.append("HIGH_RSI")

        if btc_trend == "BEARISH":
            score -= 10
            signals.append("BTC_BEARISH")
        elif btc_trend == "BULLISH":
            score += 10
            signals.append("BTC_BULLISH")

        if volatility_score is not None:
            if volatility_score > 0.8:
                score -= 10
                signals.append("HIGH_VOLATILITY_FEAR")
            elif volatility_score < 0.2:
                score += 5
                signals.append("LOW_VOLATILITY_GREED")

        if funding_rate is not None:
            if funding_rate > 0.01:
                score += 10
                signals.append("HIGH_FUNDING_GREED")
            elif funding_rate < -0.01:
                score -= 10
                signals.append("NEGATIVE_FUNDING_FEAR")

        score = max(0, min(100, round(score)))

        if score >= 75:
            label = "EXTREME_GREED"
        elif score >= 55:
            label = "GREED"
        elif score >= 45:
            label = "NEUTRAL"
        elif score >= 25:
            label = "FEAR"
        else:
            label = "EXTREME_FEAR"

        return {
            "value": score,
            "label": label,
            "signals": signals,
            "confidence": round(1.0 - abs(score - 50) / 100, 2),
            "timestamp": datetime.now(UTC).isoformat(),
        }
