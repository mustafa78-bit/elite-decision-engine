import time
from database import update_signal_status
from database import get_session, Signal
from config import CHECK_INTERVAL
from filters.btc_filter import BTCHealthFilter


class DecisionEngine:

    def __init__(self):
        print("Decision Engine initialized")
        self.btc = BTCHealthFilter()

    def get_open_signals(self):
        session = get_session()

        try:
            return (
                session.query(Signal)
                .filter(Signal.status == "OPEN")
                .all()
            )
        finally:
            session.close()

    def process_signal(self, signal):

        print("=" * 50)
        print(f"Coin      : {signal.symbol}")
        print(f"Side      : {signal.side}")
        print(f"Timeframe : {signal.timeframe}")

        if signal.side.upper() == "LONG":
            if not self.btc.is_healthy():
                print("RED -> BTC market sağlıklı değil.")
                print("=" * 50)
                return

        print("APPROVED")
        print("=" * 50)

    def run(self):

        while True:

            signals = self.get_open_signals()

            if len(signals) == 0:
                print("Bekleyen sinyal yok.")

            else:
                print(f"{len(signals)} adet yeni sinyal bulundu.")

                for signal in signals:
                    self.process_signal(signal)

            time.sleep(CHECK_INTERVAL)
