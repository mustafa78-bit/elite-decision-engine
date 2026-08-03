"""End-to-end integration tests for the real automation chain.

Verifies: Scanner opportunities -> signal_generator.generate_signals()
-> Signal(DB, OPEN) -> DecisionEngine.get_open_signals()/process_signal()
-> ExecutionLoop -> DecisionPipeline -> RiskManager -> TradeEngine
-> Trade(DB) + PaperOrder/PaperTrade journal rows.

Uses the test database configured via ``TEST_DATABASE_URL``. The
production database is never touched. Does not exercise the actual
``asyncio.to_thread`` scheduling in ``api.main``'s ``lifespan()`` --
calls ``DecisionEngine`` methods directly instead, per
``SPRINT_JULES_MEGA_AUTOMATION_E2E_TESTS.md``.
"""

import pandas as pd

from core.confidence_engine import ConfidenceEngine
from core.engine import DecisionEngine
from database import PaperOrder, PaperTrade, Signal, Trade
from execution.execution_loop import ExecutionLoop
from execution.paper import PaperExecutor as PaperDomainExecutor
from execution.paper_executor import PaperExecutor
from execution.pipeline import DecisionPipeline
from risk_manager import RiskManager
from scanner.models import Opportunity
from services.signal_generator import generate_signals


class MockCollector:
    """Returns constant close price. Satisfies MarketDataCollector protocol."""

    def __init__(self, close_price=50000.0):
        self.close_price = close_price

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return pd.DataFrame({"close": [self.close_price] * 100})


class ApprovingScoringEngine:
    """Returns scores that guarantee APPROVE (confidence >= 80) for every signal."""

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


class RejectingScoringEngine:
    """Returns scores that produce confidence = 50 (REJECT, not approved)."""

    def score(self, signal):
        return {
            "entry": 50000.0,
            "ema20": 51000.0,
            "ema50": 50500.0,
            "ema200": 50200.0,
            "rsi": 55.0,
            "atr": 500.0,
            "trend_score": 0.5,
            "volume_score": 0.5,
            "btc_score": 0.5,
            "mtf_score": 0.5,
            "risk_score": 0.5,
            "final_score": 0.55,
        }


class _FlakyRiskManager(RiskManager):
    """Real RiskManager that raises for one symbol, simulating a malformed
    candidate blowing up downstream of a successful pipeline approval."""

    def __init__(self, session_factory, bad_symbol):
        super().__init__(session_factory=session_factory)
        self.bad_symbol = bad_symbol

    def evaluate_trade(self, candidate):
        if candidate.symbol == self.bad_symbol:
            raise RuntimeError(f"simulated risk manager failure for {candidate.symbol}")
        return super().evaluate_trade(candidate)


def _make_opportunity(symbol, side, price=50000.0, score=0.9, confidence=90.0):
    return Opportunity(
        symbol=symbol,
        side=side,
        strategy="trend",
        score=score,
        confidence=confidence,
        price=price,
        trend_score=1.0,
    )


def _build_engine(session_factory, scoring_engine, risk_manager=None):
    pipeline = DecisionPipeline(
        collector=MockCollector(close_price=50000.0),
        filters=(),
        scoring_engine=scoring_engine,
        confidence_engine=ConfidenceEngine(),
    )
    paper_executor = PaperExecutor(
        collector=MockCollector(close_price=50000.0),
        session_factory=session_factory,
    )
    journal_executor = PaperExecutor(
        collector=MockCollector(close_price=50000.0),
        session_factory=session_factory,
    )
    domain_executor = PaperDomainExecutor(
        position_executor=journal_executor,
        session_factory=session_factory,
    )
    loop = ExecutionLoop(
        pipeline=pipeline,
        paper_executor=paper_executor,
        risk_manager=risk_manager or RiskManager(session_factory=session_factory),
        trade_journal=domain_executor,
    )
    return DecisionEngine(execution_loop=loop)


class TestAutomationHappyPath:
    def test_long_and_short_opportunities_produce_filled_trades(
        self, db_session, session_factory,
    ):
        opportunities = [
            _make_opportunity("BTCUSDT", "LONG"),
            _make_opportunity("ETHUSDT", "SHORT"),
        ]
        created = generate_signals(opportunities, timeframe="1h", session=db_session)
        assert created == 2

        engine = _build_engine(session_factory, ApprovingScoringEngine())
        open_signals = engine.get_open_signals()
        assert {s.symbol for s in open_signals} == {"BTCUSDT", "ETHUSDT"}

        for signal in open_signals:
            engine.process_signal(signal)

        for symbol, side in (("BTCUSDT", "LONG"), ("ETHUSDT", "SHORT")):
            signal = db_session.query(Signal).filter(Signal.symbol == symbol).first()
            assert signal.status == "EXECUTED", f"{symbol}: expected EXECUTED, got {signal.status}"

            trade = db_session.query(Trade).filter(Trade.signal_id == signal.id).first()
            assert trade is not None, f"{symbol}: Trade was not created"
            assert trade.symbol == symbol
            assert trade.side == side
            assert trade.status == "OPEN"

            paper_order = (
                db_session.query(PaperOrder).filter(PaperOrder.trade_id == trade.id).first()
            )
            assert paper_order is not None, f"{symbol}: PaperOrder was not created"
            assert paper_order.status == "FILLED"

            paper_trade = (
                db_session.query(PaperTrade)
                .filter(PaperTrade.position_id == trade.id)
                .first()
            )
            assert paper_trade is not None, f"{symbol}: PaperTrade was not created"
            assert paper_trade.quantity > 0


class TestAutomationDedup:
    def test_generate_signals_dedupes_open_signals_across_cycles(
        self, db_session, session_factory,
    ):
        opp = _make_opportunity("SOLUSDT", "LONG")

        first_created = generate_signals([opp], timeframe="1h", session=db_session)
        assert first_created == 1

        second_created = generate_signals([opp], timeframe="1h", session=db_session)
        assert second_created == 0, "Duplicate OPEN signal should not be created"

        signals = db_session.query(Signal).filter(Signal.symbol == "SOLUSDT").all()
        assert len(signals) == 1

        engine = _build_engine(session_factory, ApprovingScoringEngine())
        for signal in engine.get_open_signals():
            engine.process_signal(signal)

        signal = signals[0]
        db_session.refresh(signal)
        assert signal.status == "EXECUTED"

        third_created = generate_signals([opp], timeframe="1h", session=db_session)
        assert third_created == 1, (
            "A new signal should be allowed once the prior one is no longer OPEN"
        )


class TestAutomationRejection:
    def test_low_confidence_signal_is_rejected_without_trade(
        self, db_session, session_factory,
    ):
        opp = _make_opportunity("ADAUSDT", "LONG")
        generate_signals([opp], timeframe="1h", session=db_session)

        engine = _build_engine(session_factory, RejectingScoringEngine())
        for signal in engine.get_open_signals():
            engine.process_signal(signal)

        signal = db_session.query(Signal).filter(Signal.symbol == "ADAUSDT").first()
        assert signal.status == "REJECTED"

        trade = db_session.query(Trade).filter(Trade.signal_id == signal.id).first()
        assert trade is None
        assert db_session.query(PaperOrder).all() == []


class TestAutomationBadSignalIsolation:
    def test_one_bad_signal_does_not_block_the_rest_of_the_batch(
        self, db_session, session_factory,
    ):
        opportunities = [
            _make_opportunity("BADCOIN", "LONG"),
            _make_opportunity("GOODCOIN", "LONG"),
        ]
        created = generate_signals(opportunities, timeframe="1h", session=db_session)
        assert created == 2

        flaky_risk_manager = _FlakyRiskManager(session_factory, bad_symbol="BADCOIN")
        engine = _build_engine(
            session_factory, ApprovingScoringEngine(), risk_manager=flaky_risk_manager,
        )

        # Exercises core/engine.py's per-signal try/except in _process_open_signals().
        engine._process_open_signals()

        bad_signal = db_session.query(Signal).filter(Signal.symbol == "BADCOIN").first()
        assert bad_signal.status == "REJECTED"
        assert db_session.query(Trade).filter(Trade.signal_id == bad_signal.id).first() is None

        good_signal = db_session.query(Signal).filter(Signal.symbol == "GOODCOIN").first()
        assert good_signal.status == "EXECUTED"
        good_trade = db_session.query(Trade).filter(Trade.signal_id == good_signal.id).first()
        assert good_trade is not None

        paper_order = (
            db_session.query(PaperOrder).filter(PaperOrder.trade_id == good_trade.id).first()
        )
        assert paper_order is not None
        assert paper_order.status == "FILLED"
