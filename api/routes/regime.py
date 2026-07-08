from fastapi import APIRouter

from market_data.btc_health import BTCHealth
from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.volatility import VolatilityEngine
from scoring.regime_engine import RegimeEngine as RegimeDetector

router = APIRouter()


@router.get("/regime")
def get_regime():
    collector = HyperliquidCollector()
    indicators = IndicatorEngine()
    btc = BTCHealth()
    vol = VolatilityEngine()
    regime = RegimeDetector()

    try:
        df = collector.get_ohlcv(symbol="BTC", timeframe="1h")
        if df.empty:
            return {"error": "No market data"}

        values = indicators.calculate(df)
        btc_score = btc.score()
        vol_score = vol.score(values)
        reg = regime.detect(values)

        rsi = values["rsi"]
        ema20 = values["ema20"]
        ema50 = values["ema50"]
        ema200 = values["ema200"]

        if btc_score >= 0.7 and reg["regime"] in ("TREND",):
            trend = "BULLISH"
        elif btc_score < 0.4 or reg["regime"] == "DOWNTREND":
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"

        if vol_score["volatility"] < 0.005:
            vol_state = "LOW"
        elif vol_score["volatility"] < 0.015:
            vol_state = "NORMAL"
        else:
            vol_state = "HIGH"

        return {
            "regime": reg["regime"],
            "trend": trend,
            "volatility_state": vol_state,
            "volatility": round(vol_score["volatility"], 5),
            "btc_health": round(btc_score, 2),
            "rsi": round(rsi, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "ema200": round(ema200, 2),
        }
    except Exception as e:
        return {"error": str(e)}
