import logging

from fastapi import APIRouter

from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.btc_health import BTCHealth
from market_data.volatility import VolatilityEngine
from scoring.regime_engine import RegimeEngine


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/market")
def get_market():
    logger.info("GET /market")
    collector = HyperliquidCollector()
    indicators = IndicatorEngine()
    btc_health = BTCHealth()
    volatility = VolatilityEngine()
    regime = RegimeEngine()

    try:
        df = collector.get_ohlcv(symbol="BTC", timeframe="1h")
        if df.empty:
            logger.warning("No market data available")
            return {"error": "No market data available"}

        values = indicators.calculate(df)
        btc_score = btc_health.score()
        vol = volatility.score(values)
        reg = regime.detect(values)
        current_price = float(df["close"].iloc[-1])

        return {
            "symbol": "BTC",
            "price": current_price,
            "change_24h": None,
            "regime": reg["regime"],
            "regime_score": reg["score"],
            "volatility": vol["volatility"],
            "volatility_score": vol["score"],
            "btc_health_score": btc_score,
            "ema20": round(values["ema20"], 2),
            "ema50": round(values["ema50"], 2),
            "ema200": round(values["ema200"], 2),
            "rsi": round(values["rsi"], 2),
            "atr": round(values["atr"], 2),
        }
    except Exception as e:
        logger.error("GET /market failed: %s", e)
        return {"error": str(e)}
