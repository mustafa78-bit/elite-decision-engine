import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import get_session, Trade


def seed_trade():
    session = get_session()

    try:
        trade = Trade(
            signal_id=1,
            symbol="BTC",
            side="LONG",

            entry=65000,
            stop=64000,

            tp1=66000,
            tp2=67000,

            rr=2.5,

            pnl=0,
            status="OPEN"
        )

        session.add(trade)
        session.commit()

        print("TRADE CREATED ✔")

    finally:
        session.close()


if __name__ == "__main__":
    seed_trade()
