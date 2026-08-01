import logging
from typing import Any, Optional

from config import SCORE_WEIGHTS
from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.volume import VolumeEngine
from market_data.btc_health import BTCHealth
from market_data.volatility import VolatilityEngine
from market_data.mtf import MTFEngine
from scoring.risk_engine import RiskEngine


logger = logging.getLogger(__name__)


class ScoringEngine:

    def __init__(self, collector: Optional[Any] = None, market_service: Optional[Any] = None):
        self.collector = collector or HyperliquidCollector()
        self.market_service = market_service
        self.indicators = IndicatorEngine()
        self.volume = VolumeEngine()
        self.btc = BTCHealth()
        self.volatility = VolatilityEngine()
        self.mtf = MTFEngine()
        self.risk = RiskEngine()

    def score(self, signal):

        coin = signal.symbol.replace("USDT", "")

        try:
            if self.market_service is not None:
                indicators = self.market_service.get_indicators(signal.symbol, signal.timeframe)
                if not indicators:
                    logger.warning("No cached indicators for %s %s, falling back", coin, signal.timeframe)
                    return self._score_fallback()

                df = self.market_service.get_ohlcv(signal.symbol, signal.timeframe)
                values = indicators
                volume = {"score": indicators.get("volume_score", 0)}
                btc_score = self.btc.score()
                volatility = {"score": indicators.get("volatility_score", 0), "volatility": indicators.get("volatility", 0)}
                mtf_score = self.mtf.score(signal.symbol, signal.side)
            else:
                df = self.collector.get_ohlcv(
                    symbol=coin,
                    timeframe=signal.timeframe,
                )

                if df is None or df.empty:
                    logger.warning("Empty market data for %s %s, returning fallback scores", coin, signal.timeframe)
                    return self._score_fallback()

                values = self.indicators.calculate(df)
                volume = self.volume.score(df)
                btc_score = self.btc.score()
                volatility = self.volatility.score(values)
                mtf_score = self.mtf.score(signal.symbol, signal.side)

        except Exception as e:
            logger.error("MARKET DATA ERROR: %s", e)
            return self._score_fallback()

        ema20 = values.get("ema20", 0)
        ema50 = values.get("ema50", 0)
        ema200 = values.get("ema200", 0)
        rsi = values.get("rsi", 50)
        atr = values.get("atr", 0)

        entry = float(df["close"].iloc[-1]) if not df.empty and "close" in df.columns else 0.0

        trend_score = 0.0

        if signal.side.upper() == "LONG":
            if ema20 > ema50:
                trend_score += 0.5
            if ema50 > ema200:
                trend_score += 0.5
        else:
            if ema20 < ema50:
                trend_score += 0.5
            if ema50 < ema200:
                trend_score += 0.5

        volume_score = volume.get("score", 0)
        risk_score = self.risk.score(values, volatility)

        final_score = (
            trend_score * SCORE_WEIGHTS["trend"] +
            volume_score * SCORE_WEIGHTS["volume"] +
            btc_score * SCORE_WEIGHTS["btc"] +
            mtf_score * SCORE_WEIGHTS["mtf"] +
            risk_score * SCORE_WEIGHTS["risk"]
        )

        logger.debug(
            "Scores for %s %s: trend=%.2f vol=%.2f btc=%.2f mtf=%.2f risk=%.2f final=%.3f",
            signal.symbol, signal.side,
            trend_score, volume_score, btc_score, mtf_score, risk_score, final_score,
        )

        return {
            "entry": entry,
            "ema20": ema20,
            "ema50": ema50,
            "ema200": ema200,
            "rsi": rsi,
            "atr": atr,
            "trend_score": round(trend_score, 2),
            "volume_score": round(volume_score, 2),
            "btc_score": round(btc_score, 2),
            "mtf_score": round(mtf_score, 2),
            "risk_score": round(risk_score, 2),
            "final_score": round(final_score, 3),
            "contributions": {
                "trend": round(trend_score * SCORE_WEIGHTS["trend"], 4),
                "volume": round(volume_score * SCORE_WEIGHTS["volume"], 4),
                "btc": round(btc_score * SCORE_WEIGHTS["btc"], 4),
                "mtf": round(mtf_score * SCORE_WEIGHTS["mtf"], 4),
                "risk": round(risk_score * SCORE_WEIGHTS["risk"], 4),
            },
        }

    @staticmethod
    def _score_fallback() -> dict[str, Any]:
        return {
            "volume_score": 0,
            "trend_score": 0,
            "btc_score": 0,
            "mtf_score": 0,
            "risk_score": 1,
            "final_score": 0,
        }
