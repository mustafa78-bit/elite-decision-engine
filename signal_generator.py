import time
import random
from database import get_session, Signal

symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def create_signal():
    session = get_session()

    signal = Signal(
        symbol=random.choice(symbols),
        side=random.choice(["LONG", "SHORT"]),
        timeframe="1h",
        divergence="AUTO_GEN",
        price=round(random.uniform(20000, 70000), 2),
        status="OPEN"
    )

    session.add(signal)
    session.commit()
    session.close()

    print("NEW SIGNAL CREATED")

if __name__ == "__main__":
    while True:
        create_signal()
        time.sleep(10)
