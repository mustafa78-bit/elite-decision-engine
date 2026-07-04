from database import get_session, Trade


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

    def run(self):

        trades = self.get_open_trades()

        print("=" * 50)
        print(f"OPEN TRADES : {len(trades)}")

        for trade in trades:
            print(
                f"{trade.symbol} | "
                f"{trade.side} | "
                f"ENTRY={trade.entry} | "
                f"STOP={trade.stop} | "
                f"TP1={trade.tp1}"
            )
