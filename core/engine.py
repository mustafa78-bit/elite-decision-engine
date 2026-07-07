import time

from config import CHECK_INTERVAL
from database import Signal, get_session, update_signal_status
from execution.execution_loop import ExecutionLoop


class DecisionEngine:

    def __init__(self, execution_loop=None):
        print("Decision Engine initialized")
        self.execution_loop = execution_loop or ExecutionLoop()

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

            self.execution_loop.run_once([signal])
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
