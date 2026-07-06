import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import get_session, Trade


def generate_signal():
    session = get_session()

    try:
        # basit fake market logic (sonra gerçek data bağlanacak)
        price = 65000

        trade = Trade(
            signal_id=999,
            symbol="BTC",
            side="LONG",

            entry=price,
            stop=price - 1000,
            tp1=price + 1000,
            tp2=price + 2000,

            rr=2.0,
            status="OPEN"
        )

        session.add(trade)
        session.commit()

        print("SIGNAL → TRADE CREATED ✔")

    finally:
        session.close()


if __name__ == "__main__":
    generate_signal()
