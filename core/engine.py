import time

from database import get_session, Signal, update_signal_status
from config import CHECK_INTERVAL
from filters.btc_filter import BTCHealthFilter
from scoring.scoring_engine import ScoringEngine


class DecisionEngine:

    def __init__(self):
        print("Decision Engine initialized")
        self.btc = BTCHealthFilter()
        self.scorer = ScoringEngine()

    def get_open_signals(self):
        session = get_session()
        try:
            return session.query(Signal).filter(Signal.status == "OPEN").all()
        finally:
            session.close()

    def process_signal(self, signal):

        try:
            print("=" * 50)
            print(f"Coin      : {signal.symbol}")
            print(f"Side      : {signal.side}")
            print(f"Timeframe : {signal.timeframe}")

            update_signal_status(signal.id, "PROCESSING")

            scores = self.scorer.score(signal)
            score = scores["final_score"]

            print("SCORE:", score)

            if score < 0.55:
                update_signal_status(signal.id, "REJECTED")
                print("REJECTED")
                return

            if score < 0.65:
                update_signal_status(signal.id, "WATCH")
                print("WATCH")
                return

            if score < 0.80:
                update_signal_status(signal.id, "APPROVED")
                print("APPROVED")
                return

            update_signal_status(signal.id, "STRONG_APPROVE")
            print("STRONG APPROVE")

        except Exception as e:
            print("ERROR:", e)
            update_signal_status(signal.id, "REJECTED")

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
