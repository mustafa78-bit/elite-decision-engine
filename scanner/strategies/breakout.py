from __future__ import annotations

from typing import Any

import pandas as pd
import pandas_ta as ta

from config import SCANNER_SQUEEZE_BONUS, SCANNER_SQUEEZE_WIDTH_RATIO


def _bollinger_band_width(closes: pd.Series) -> pd.Series | None:
    """Bollinger Band width (upper-lower)/middle as a series -- narrower
    means more compressed volatility. Returns None if pandas_ta can't
    compute bands (e.g. too few candles or a degenerate/flat series)."""
    bb = ta.bbands(closes, length=20, std=2.0)
    if bb is None or bb.empty:
        return None
    upper_col = next((c for c in bb.columns if c.startswith("BBU")), None)
    lower_col = next((c for c in bb.columns if c.startswith("BBL")), None)
    middle_col = next((c for c in bb.columns if c.startswith("BBM")), None)
    if not (upper_col and lower_col and middle_col):
        return None
    return (bb[upper_col] - bb[lower_col]) / bb[middle_col]


class BreakoutStrategy:
    """Score breakout opportunities using price vs EMA and volume confirmation."""

    name = "breakout"

    MIN_LOOKBACK = 20
    SQUEEZE_MIN_CANDLES = 30

    def evaluate(self, asset: Any) -> tuple[float, list[str]]:
        indicators = asset.indicators
        signals: list[str] = []

        ohlcv = asset.ohlcv
        if ohlcv is None or len(ohlcv) < self.MIN_LOOKBACK:
            return 0.0, signals

        ema20 = indicators.get("ema20", 0)
        price = asset.price
        if ema20 <= 0 or price <= 0:
            return 0.0, signals

        closes = ohlcv["close"].values
        volumes = ohlcv["volume"].values

        recent = closes[-5:]
        prior = closes[-self.MIN_LOOKBACK:-5]

        score_long = 0.0
        score_short = 0.0

        if len(prior) > 0:
            prior_max = float(max(prior))
            if price > prior_max and price > ema20:
                score_long += 0.5
                signals.append("PRICE_BREAKOUT_HIGH")

            prior_min = float(min(prior))
            if price < prior_min and price < ema20:
                score_short += 0.5
                signals.append("PRICE_BREAKOUT_LOW")

        avg_volume = float(volumes[-self.MIN_LOOKBACK:].mean())
        current_volume = float(volumes[-1])
        if avg_volume > 0 and current_volume > avg_volume * 1.5:
            if score_long > score_short:
                score_long += 0.3
            elif score_short > score_long:
                score_short += 0.3
            else:
                if price >= ema20:
                    score_long += 0.3
                else:
                    score_short += 0.3
            signals.append("HIGH_VOLUME_CONFIRMATION")

        if len(prior) > 0 and len(recent) > 0:
            if float(recent[-1]) > ema20 and float(prior[-1]) <= ema20:
                score_long += 0.2
                signals.append("EMA_CROSSOVER")
            elif float(recent[-1]) < ema20 and float(prior[-1]) >= ema20:
                score_short += 0.2
                signals.append("EMA_CROSSUNDER")

        # Squeeze-confirmed breakout: only rewards a real directional
        # breakout already found above -- a squeeze with no breakout
        # direction to confirm isn't scored here at all.
        if len(ohlcv) >= self.SQUEEZE_MIN_CANDLES and (score_long != score_short):
            bb_width = _bollinger_band_width(ohlcv["close"])
            if bb_width is not None:
                avg_width = bb_width.tail(50).mean()
                # Excludes the current/breakout candle -- its width is
                # already expanding by the time price clears the range,
                # so only the candles *before* it count as "was squeezed".
                pre_breakout_width = bb_width.iloc[-11:-1]
                if pd.notna(avg_width) and avg_width > 0 and not pre_breakout_width.empty:
                    min_pre_width = pre_breakout_width.min()
                    if pd.notna(min_pre_width) and min_pre_width < avg_width * SCANNER_SQUEEZE_WIDTH_RATIO:
                        signals.append("SQUEEZE_RELEASE")
                        if score_long > score_short:
                            score_long += SCANNER_SQUEEZE_BONUS
                        else:
                            score_short += SCANNER_SQUEEZE_BONUS

        if score_long >= score_short:
            return round(min(score_long, 1.0), 4), signals
        else:
            return -round(min(score_short, 1.0), 4), signals
