"""End-to-end integration test for the paper trading execution path.

Verifies:
  Signal -> DecisionEngine -> ExecutionLoop -> DecisionPipeline
  -> TradeEngine -> Trade(DB) -> PaperExecutor -> TP/SL -> Trade Close

Run: python test_integration.py
"""

import pandas as pd
from database import get_session, Signal, Trade
from execution.execution_loop import ExecutionLoop
from execution.pipeline import DecisionPipeline
from execution.trade_engine import TradeEngine
from execution.paper_executor import PaperExecutor
from core.engine import DecisionEngine
from core.confidence_engine import ConfidenceEngine


class MockCollector:
    """Returns constant close price. Satisfies MarketDataCollector protocol."""

    def __init__(self, close_price=50000.0):
        self.close_price = close_price

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return pd.DataFrame({"close": [self.close_price] * 100})


class MockScoringEngine:
    """Returns scores that guarantee APPROVE (confidence >= 80)."""

    def score(self, signal):
        return {
            "entry": 50000.0,
            "ema20": 51000.0,
            "ema50": 50500.0,
            "ema200": 50200.0,
            "rsi": 55.0,
            "atr": 500.0,
            "trend_score": 1.0,
            "volume_score": 1.0,
            "btc_score": 1.0,
            "mtf_score": 1.0,
            "risk_score": 0.0,
            "final_score": 0.9,
        }


def test_end_to_end_paper_trading():
    """Create a signal, process it through the full pipeline, verify trade creation,
    TP/SL monitoring, and trade close."""
    session = get_session()
    signal_id = None
    trade_id = None

    try:
        # ---- Phase 1: Create test signal ----
        signal = Signal(
            symbol="BTCUSDT",
            side="LONG",
            timeframe="1h",
            status="OPEN",
        )
        session.add(signal)
        session.commit()
        signal_id = signal.id
        print(f"[SIGNAL] Created test signal id={signal_id}")

        # ---- Phase 2: Build pipeline with mocked dependencies ----
        pipeline = DecisionPipeline(
            collector=MockCollector(close_price=50000.0),
            filters=(),
            scoring_engine=MockScoringEngine(),
            confidence_engine=ConfidenceEngine(),
        )

        paper_executor = PaperExecutor(
            collector=MockCollector(close_price=50000.0),
        )

        loop = ExecutionLoop(
            pipeline=pipeline,
            paper_executor=paper_executor,
        )

        engine = DecisionEngine(execution_loop=loop)

        # ---- Phase 3: Process signal ----
        engine.process_signal(signal)

        # ---- Phase 4: Verify trade created ----
        session.refresh(signal)
        trade = session.query(Trade).filter(Trade.signal_id == signal_id).first()
        assert trade is not None, "Trade was not created"
        trade_id = trade.id

        assert trade.status == "OPEN", f"Expected OPEN, got {trade.status}"
        assert trade.symbol == "BTCUSDT"
        assert trade.side == "LONG"
        assert trade.entry == 50000.0
        assert trade.stop == 49250.0
        assert trade.tp1 == 51000.0
        assert abs(trade.rr - 1.33) < 0.01
        assert signal.status == "EXECUTED", f"Expected EXECUTED, got {signal.status}"
        print(f"[TRADE] Created id={trade.id} entry={trade.entry} "
              f"stop={trade.stop} tp1={trade.tp1} rr={trade.rr}")

        # ---- Phase 5: Monitor at price above TP (LONG: entry=50000, TP1=51000) ----
        monitor_executor = PaperExecutor(
            collector=MockCollector(close_price=52000.0),
        )
        results = monitor_executor.monitor_open_trades()

        our_result = next((r for r in results if r.trade_id == trade_id), None)
        assert our_result is not None, f"Trade {trade_id} not found in monitor results"
        assert our_result.status == "TP_HIT", f"Expected TP_HIT, got {our_result.status}"
        print(f"[MONITOR] Trade id={our_result.trade_id} status={our_result.status}")

        # ---- Phase 6: Verify trade closed in DB ----
        session.expire_all()
        closed = session.query(Trade).filter(Trade.id == trade_id).first()
        assert closed.status == "TP_HIT", f"Expected TP_HIT, got {closed.status}"
        assert closed.exit_price == 52000.0
        assert closed.close_reason == "TP_HIT"
        print(f"[CLOSE] Trade id={closed.id} status={closed.status} "
              f"exit={closed.exit_price} reason={closed.close_reason}")

        print("\n=== ALL INTEGRATION TESTS PASSED ===")

    except AssertionError as e:
        print(f"\nFAILED: {e}")
        raise

    finally:
        if trade_id is not None:
            session.query(Trade).filter(Trade.id == trade_id).delete()
        if signal_id is not None:
            session.query(Signal).filter(Signal.id == signal_id).delete()
        session.commit()
        session.close()


if __name__ == "__main__":
    test_end_to_end_paper_trading()
