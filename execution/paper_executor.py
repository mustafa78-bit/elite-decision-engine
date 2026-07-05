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

        trades = self.get_open_trades()

        print("=" * 50)
        print(f"OPEN TRADES : {len(trades)}")

        for trade in trades:

            price = self.get_current_price(trade.symbol)

            print(f"CURRENT={price}")

            print(
                f"{trade.symbol} | "
                f"{trade.side} | "
                f"ENTRY={trade.entry} | "
                f"STOP={trade.stop} | "
                f"TP1={trade.tp1}"
            )
