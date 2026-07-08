import logging
import sys
import os
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import get_session, Trade
from market_data.collector import HyperliquidCollector

logger = logging.getLogger(__name__)


class LiveSignalEngine:
    def __init__(self, collector: Optional[Any] = None):
        self.collector = collector or HyperliquidCollector()

    def generate_signal(self):
        session = get_session()

        try:
            df = self.collector.get_ohlcv("BTC", "1h", 50)

            if df.empty:
                logger.warning("No market data received")
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

            logger.info("Live signal generated: %s @ %.2f", side, price)

        finally:
            session.close()


if __name__ == "__main__":
    engine = LiveSignalEngine()
    engine.generate_signal()
