import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import get_session, Trade
from market_data.collector import HyperliquidCollector


class LiveSignalEngine:
    def __init__(self):
        self.collector = HyperliquidCollector()

    def generate_signal(self):
        session = get_session()

        try:
            df = self.collector.get_ohlcv("BTC", "1h", 50)

            if df.empty:
                print("NO DATA")
                return

            last = df.iloc[-1]
            price = float(last["close"])

            # basit trend logic
            prev = df.iloc[-2]

            if price > float(prev["close"]):
                side = "LONG"
                sl = price * 0.99
                tp1 = price * 1.01
                tp2 = price * 1.02
            else:
                side = "SHORT"
                sl = price * 1.01
                tp1 = price * 0.99
                tp2 = price * 0.98

            trade = Trade(
                signal_id=777,
                symbol="BTC",
                side=side,
                entry=price,
                stop=sl,
                tp1=tp1,
                tp2=tp2,
                rr=2.0,
                status="OPEN"
            )

            session.add(trade)
            session.commit()

            print(f"LIVE SIGNAL ✔ | {side} @ {price}")

        finally:
            session.close()


if __name__ == "__main__":
    engine = LiveSignalEngine()
    engine.generate_signal()
