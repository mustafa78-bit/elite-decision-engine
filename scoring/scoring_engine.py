from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.volume import VolumeEngine
from market_data.btc_health import BTCHealth
from market_data.volatility import VolatilityEngine
from market_data.mtf import MTFEngine
from scoring.risk_engine import RiskEngine


class ScoringEngine:

    def __init__(self):
        self.collector = HyperliquidCollector()
        self.indicators = IndicatorEngine()
        self.volume = VolumeEngine()
        self.btc = BTCHealth()
        self.volatility = VolatilityEngine()
        self.mtf = MTFEngine()
        self.risk = RiskEngine()

    def score(self, signal):

        coin = signal.symbol.replace("USDT", "")

        try:
            df = self.collector.get_ohlcv(
                symbol=coin,
                timeframe=signal.timeframe,
            )

            values = self.indicators.calculate(df)
            volume = self.volume.score(df)
            btc_score = self.btc.score()
            volatility = self.volatility.score(values)
            mtf_score = self.mtf.score(signal.symbol, signal.side)

        except Exception as e:
            print("MARKET DATA ERROR:", e)
            return {
                "volume_score": 0,
                "trend_score": 0,
                "btc_score": 0,
                "mtf_score": 0,
                "risk_score": 1,
                "final_score": 0,
            }

        ema20 = values["ema20"]
        ema50 = values["ema50"]
        ema200 = values["ema200"]
        rsi = values["rsi"]
        atr = values["atr"]

        entry = float(df["close"].iloc[-1])

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

        volume_score = volume["score"]
        risk_score = self.risk.score(values, volatility)

        final_score = (
            trend_score * 0.30 +
            volume_score * 0.20 +
            btc_score * 0.20 +
            mtf_score * 0.20 +
            risk_score * 0.10
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
        }
