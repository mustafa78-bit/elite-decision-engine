from market.provider import get_shared_multi_provider
from market_data.indicators import IndicatorEngine


class MTFEngine:

    def __init__(self):
        self.collector = get_shared_multi_provider()
        self.indicators = IndicatorEngine()

    def score(self, symbol, side):

        # Do NOT strip "USDT" here -- self.collector is MultiProvider, which
        # needs the full ticker symbol (e.g. "TAOUSDT") to look up
        # config.SYMBOL_PROVIDER_ASSIGNMENT and route to the correct
        # exchange. A bare "TAO" is never a key in that table, so it always
        # silently fell through to the "hyperliquid" default regardless of
        # the symbol's real assignment -- confirmed live 2026-08-20: roughly
        # half of all real Hyperliquid 429s were for symbols assigned to
        # Binance/Bybit, not Hyperliquid, entirely because of this. Each
        # underlying provider (Hyperliquid/Binance/Bybit) already accepts
        # the full ticker symbol and strips/formats it itself as needed.
        timeframes = ["15m", "1h", "4h"]

        score = 0

        for tf in timeframes:

            df = self.collector.get_ohlcv(
                symbol=symbol,
                timeframe=tf,
            )

            ind = self.indicators.calculate(df)

            if side == "LONG":
                if ind["ema20"] > ind["ema50"] > ind["ema200"]:
                    score += 1
            else:
                if ind["ema20"] < ind["ema50"] < ind["ema200"]:
                    score += 1

        return round(score / len(timeframes), 2)
