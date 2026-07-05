from database import get_session, Trade
from market_data.collector import HyperliquidCollector


class PaperExecutor:

    def get_open_trades(self):
        session = get_session()

        try:
            return (
                session.query(Trade)
                .filter(Trade.status == "OPEN")
                .all()
            )

        finally:
            session.close()

    def get_current_price(self, symbol):

        collector = HyperliquidCollector()

        df = collector.get_ohlcv(
            symbol=symbol,
            timeframe="1h",
            limit=1,
        )

        if df.empty:
            return None

        return float(df.iloc[-1]["close"])

    def run(self):

        session = get_session()

        try:

            trades = (
                session.query(Trade)
                .filter(Trade.status == "OPEN")
                .all()
            )

            print("=" * 50)
            print(f"OPEN TRADES : {len(trades)}")

            for trade in trades:

                price = self.get_current_price(trade.symbol)

                if price is None:
                    continue

                print(
                    f"{trade.symbol} | "
                    f"PRICE={price} | "
                    f"ENTRY={trade.entry} | "
                    f"STOP={trade.stop} | "
                    f"TP1={trade.tp1} | "
                    f"TP2={trade.tp2}"
                )

        finally:
            session.close()
