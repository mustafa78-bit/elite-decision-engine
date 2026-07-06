import time

from config import CHECK_INTERVAL
from database import Signal, get_session, update_signal_status
from execution.execution_loop import ExecutionLoop
from execution.pipeline import TradeCandidate
from execution.trade_engine import TradeEngine
from scoring.scoring_engine import ScoringEngine


class DecisionEngine:

    def __init__(self):
        print("Decision Engine initialized")
        self.scorer = ScoringEngine()
        self.trade_engine = TradeEngine()
        self.execution_loop = ExecutionLoop(trade_engine=self.trade_engine)

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

                self.execution_loop.run_once(
                    self._build_trade_candidate(
                        signal=signal,
                        scores=scores,
                        decision="APPROVED",
                    )
                )

                return

            update_signal_status(signal.id, "STRONG_APPROVE")
            print("STRONG APPROVE")

            self.execution_loop.run_once(
                self._build_trade_candidate(
                    signal=signal,
                    scores=scores,
                    decision="STRONG_APPROVE",
                )
            )
        except Exception as e:
            print("ERROR:", e)
            update_signal_status(signal.id, "REJECTED")

    @staticmethod
    def _build_trade_candidate(
        signal: Signal,
        scores,
        decision: str,
    ) -> TradeCandidate:
        return TradeCandidate(
            symbol=signal.symbol,
            side=signal.side,
            timeframe=signal.timeframe,
            entry=scores["entry"],
            scores=scores,
            confidence=0.0,
            decision=decision,
            signal=signal,
        )

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
