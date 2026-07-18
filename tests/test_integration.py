"""End-to-end integration test for the paper trading execution path.

Verifies:
  Signal -> DecisionEngine -> ExecutionLoop -> DecisionPipeline
  -> TradeEngine -> Trade(DB) -> PaperExecutor -> TP/SL -> Trade Close

Uses the test database configured via ``TEST_DATABASE_URL``.
The production database is never touched.
"""

import pandas as pd
import pytest
from database import Signal, Trade
from execution.execution_loop import ExecutionLoop
from execution.pipeline import DecisionPipeline
from execution.paper_executor import PaperExecutor
from core.engine import DecisionEngine
from core.confidence_engine import ConfidenceEngine
from risk_manager import RiskManager


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


class _LowScoreEngine:
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


def _build_pipeline(collector=None, scoring_engine=None):
    return DecisionPipeline(
        collector=collector or MockCollector(close_price=50000.0),
        filters=(),
        scoring_engine=scoring_engine or MockScoringEngine(),
        confidence_engine=ConfidenceEngine(),
    )


def _build_executor(collector, session_factory):
    return PaperExecutor(
        collector=collector,
        session_factory=session_factory,
    )


def _build_loop(pipeline, executor, session_factory):
    return ExecutionLoop(
        pipeline=pipeline,
        paper_executor=executor,
        risk_manager=RiskManager(session_factory=session_factory),
    )


def test_end_to_end_paper_trading(db_session, session_factory):
    """Create a signal, process it through the full pipeline, verify trade creation,
    TP/SL monitoring, and trade close."""

    signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
    db_session.add(signal)
    db_session.flush()
    signal_id = signal.id

    pipeline = _build_pipeline()
    executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
    loop = _build_loop(pipeline, executor, session_factory)
    engine = DecisionEngine(execution_loop=loop)

    engine.process_signal(signal)

    db_session.refresh(signal)
    trade = db_session.query(Trade).filter(Trade.signal_id == signal_id).first()
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

    monitor_executor = PaperExecutor(
        collector=MockCollector(close_price=52000.0),
        session_factory=session_factory,
    )
    results = monitor_executor.monitor_open_trades()

    our_result = next((r for r in results if r.trade_id == trade_id), None)
    assert our_result is not None, f"Trade {trade_id} not found in monitor results"
    assert our_result.status == "TP_HIT", f"Expected TP_HIT, got {our_result.status}"

    db_session.expire_all()
    closed = db_session.query(Trade).filter(Trade.id == trade_id).first()
    assert closed.status == "TP_HIT", f"Expected TP_HIT, got {closed.status}"
    assert closed.exit_price == 52000.0
    assert closed.close_reason == "TP_HIT"


def test_long_sl_hit(db_session, session_factory):
    """LONG trade is closed when price hits the stop loss."""

    signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
    db_session.add(signal)
    db_session.flush()
    signal_id = signal.id

    pipeline = _build_pipeline()
    executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
    loop = _build_loop(pipeline, executor, session_factory)
    DecisionEngine(execution_loop=loop).process_signal(signal)

    trade = db_session.query(Trade).filter(Trade.signal_id == signal_id).first()
    assert trade is not None
    trade_id = trade.id

    monitor_executor = PaperExecutor(
        collector=MockCollector(close_price=49000.0),
        session_factory=session_factory,
    )
    results = monitor_executor.monitor_open_trades()

    our_result = next((r for r in results if r.trade_id == trade_id), None)
    assert our_result is not None
    assert our_result.status == "SL_HIT", f"Expected SL_HIT, got {our_result.status}"

    db_session.expire_all()
    closed = db_session.query(Trade).filter(Trade.id == trade_id).first()
    assert closed.status == "SL_HIT"
    assert closed.close_reason == "SL_HIT"


def test_short_tp_hit(db_session, session_factory):
    """SHORT trade is created and closed when price hits TP."""

    signal = Signal(symbol="BTCUSDT", side="SHORT", timeframe="1h", status="OPEN")
    db_session.add(signal)
    db_session.flush()
    signal_id = signal.id

    pipeline = _build_pipeline()
    executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
    loop = _build_loop(pipeline, executor, session_factory)
    DecisionEngine(execution_loop=loop).process_signal(signal)

    db_session.refresh(signal)
    assert signal.status == "EXECUTED", f"Expected EXECUTED, got {signal.status}"

    trade = db_session.query(Trade).filter(Trade.signal_id == signal_id).first()
    assert trade is not None, "SHORT trade was not created"
    trade_id = trade.id

    assert trade.side == "SHORT"
    assert trade.stop == 50750.0
    assert trade.tp1 == 49000.0

    monitor_executor = PaperExecutor(
        collector=MockCollector(close_price=48000.0),
        session_factory=session_factory,
    )
    results = monitor_executor.monitor_open_trades()

    our_result = next((r for r in results if r.trade_id == trade_id), None)
    assert our_result is not None
    assert our_result.status == "TP_HIT", f"Expected TP_HIT, got {our_result.status}"

    db_session.expire_all()
    closed = db_session.query(Trade).filter(Trade.id == trade_id).first()
    assert closed.status == "TP_HIT"
    assert closed.side == "SHORT"


def test_short_sl_hit(db_session, session_factory):
    """SHORT trade is closed when price hits the stop loss."""

    signal = Signal(symbol="BTCUSDT", side="SHORT", timeframe="1h", status="OPEN")
    db_session.add(signal)
    db_session.flush()
    signal_id = signal.id

    pipeline = _build_pipeline()
    executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
    loop = _build_loop(pipeline, executor, session_factory)
    DecisionEngine(execution_loop=loop).process_signal(signal)

    trade = db_session.query(Trade).filter(Trade.signal_id == signal_id).first()
    assert trade is not None
    trade_id = trade.id

    monitor_executor = PaperExecutor(
        collector=MockCollector(close_price=51000.0),
        session_factory=session_factory,
    )
    results = monitor_executor.monitor_open_trades()

    our_result = next((r for r in results if r.trade_id == trade_id), None)
    assert our_result is not None
    assert our_result.status == "SL_HIT", f"Expected SL_HIT, got {our_result.status}"

    db_session.expire_all()
    closed = db_session.query(Trade).filter(Trade.id == trade_id).first()
    assert closed.status == "SL_HIT"


def test_pipeline_rejects_low_scores(db_session, session_factory):
    """Signal is REJECTED when pipeline confidence is too low."""

    signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
    db_session.add(signal)
    db_session.flush()
    signal_id = signal.id

    pipeline = _build_pipeline(scoring_engine=_LowScoreEngine())
    executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
    loop = _build_loop(pipeline, executor, session_factory)
    DecisionEngine(execution_loop=loop).process_signal(signal)

    db_session.refresh(signal)
    assert signal.status == "REJECTED", f"Expected REJECTED, got {signal.status}"

    trade = db_session.query(Trade).filter(Trade.signal_id == signal_id).first()
    assert trade is None, "Trade should not be created for rejected signal"


def test_signal_risk_execution_flow(db_session, session_factory, monkeypatch):
    """Integration: Signal → RiskManager.evaluate_trade → structured decision."""
    from risk_manager import RiskManager
    from risk.models import RiskDecision, RejectionCode

    monkeypatch.setattr("risk_manager.MAX_OPEN_TRADES", 0)

    signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
    db_session.add(signal)
    db_session.flush()
    signal_id = signal.id

    pipeline = _build_pipeline()
    executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
    loop = _build_loop(pipeline, executor, session_factory)
    engine = DecisionEngine(execution_loop=loop)
    engine.process_signal(signal)

    db_session.refresh(signal)
    assert signal.status == "REJECTED"
    trade = db_session.query(Trade).filter(Trade.signal_id == signal_id).first()
    assert trade is None

    class _Candidate:
        def __init__(self):
            self.symbol = "BTCUSDT"
            self.entry = 50000.0

    rm = RiskManager(session_factory=session_factory)
    decision = rm.evaluate_trade(_Candidate())
    assert isinstance(decision, RiskDecision)
    assert decision.allowed is False
    assert decision.rejection_code == RejectionCode.MAX_OPEN_TRADES
    assert len(decision.checks) > 0
    for c in decision.checks:
        assert isinstance(c.passed, bool)
        if not c.passed:
            assert c.detail != ""


def test_risk_manager_rejects(db_session, session_factory, monkeypatch):
    """Signal is REJECTED when risk manager blocks the trade."""

    monkeypatch.setattr("risk_manager.MAX_OPEN_TRADES", 0)

    signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
    db_session.add(signal)
    db_session.flush()
    signal_id = signal.id

    pipeline = _build_pipeline()
    executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
    loop = _build_loop(pipeline, executor, session_factory)
    DecisionEngine(execution_loop=loop).process_signal(signal)

    db_session.refresh(signal)
    assert signal.status == "REJECTED", f"Expected REJECTED, got {signal.status}"

    trade = db_session.query(Trade).filter(Trade.signal_id == signal_id).first()
    assert trade is None, "Trade should not be created when risk rejects"


# ===========================================================================
# Paper Trade Journal Integration
# ===========================================================================


class TestPaperTradeJournalIntegration:
    """Signal → PaperOrder → Fill → PaperPosition → PaperTrade journal."""

    def test_signal_to_paper_order(
        self, db_session, session_factory,
    ):
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        pipeline = _build_pipeline()
        executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
        journal = _build_executor(MockCollector(close_price=50000.0), session_factory)
        from execution.paper import PaperExecutor as PaperDomainExecutor
        domain_executor = PaperDomainExecutor(
            position_executor=journal,
            session_factory=session_factory,
        )
        loop = ExecutionLoop(
            pipeline=pipeline,
            paper_executor=executor,
            risk_manager=RiskManager(session_factory=session_factory),
            trade_journal=domain_executor,
        )
        engine = DecisionEngine(execution_loop=loop)
        engine.process_signal(signal)

        db_session.refresh(signal)
        trade = db_session.query(Trade).filter(Trade.signal_id == signal.id).first()
        assert trade is not None

        from database import PaperOrder as PaperOrderModel
        paper_order = (
            db_session.query(PaperOrderModel)
            .filter(PaperOrderModel.trade_id == trade.id)
            .first()
        )
        assert paper_order is not None, "PaperOrder should be created"
        assert paper_order.status == "FILLED", f"Expected FILLED, got {paper_order.status}"
        assert paper_order.symbol == "BTCUSDT"
        assert paper_order.side == "LONG"

    def test_order_to_fill(
        self, db_session, session_factory,
    ):
        signal = Signal(symbol="ETHUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        pipeline = _build_pipeline()
        executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
        journal = _build_executor(MockCollector(close_price=50000.0), session_factory)
        from execution.paper import PaperExecutor as PaperDomainExecutor
        domain_executor = PaperDomainExecutor(
            position_executor=journal,
            session_factory=session_factory,
        )
        loop = ExecutionLoop(
            pipeline=pipeline,
            paper_executor=executor,
            risk_manager=RiskManager(session_factory=session_factory),
            trade_journal=domain_executor,
        )
        DecisionEngine(execution_loop=loop).process_signal(signal)

        trade = db_session.query(Trade).filter(Trade.signal_id == signal.id).first()
        assert trade is not None

        from database import PaperOrder as PaperOrderModel
        from database import PaperTrade as PaperTradeModel
        paper_order = (
            db_session.query(PaperOrderModel)
            .filter(PaperOrderModel.trade_id == trade.id)
            .first()
        )
        assert paper_order is not None
        assert paper_order.filled_price == 50000.0
        assert paper_order.filled_quantity is not None
        assert paper_order.filled_quantity > 0
        assert paper_order.status == "FILLED"

        paper_trade = (
            db_session.query(PaperTradeModel)
            .filter(PaperTradeModel.position_id == trade.id)
            .first()
        )
        assert paper_trade is not None, "PaperTrade should be created"
        assert paper_trade.entry == 50000.0
        assert paper_trade.quantity > 0
        assert paper_trade.status == "OPEN"
        assert paper_trade.order_id == paper_order.id

    def test_fill_to_position_link(
        self, db_session, session_factory,
    ):
        signal = Signal(symbol="SOLUSDT", side="SHORT", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        pipeline = _build_pipeline()
        executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
        journal = _build_executor(MockCollector(close_price=50000.0), session_factory)
        from execution.paper import PaperExecutor as PaperDomainExecutor
        domain_executor = PaperDomainExecutor(
            position_executor=journal,
            session_factory=session_factory,
        )
        loop = ExecutionLoop(
            pipeline=pipeline,
            paper_executor=executor,
            risk_manager=RiskManager(session_factory=session_factory),
            trade_journal=domain_executor,
        )
        DecisionEngine(execution_loop=loop).process_signal(signal)

        trade = db_session.query(Trade).filter(Trade.signal_id == signal.id).first()
        assert trade is not None
        assert trade.status == "OPEN"

        from database import PaperTrade as PaperTradeModel
        paper_trade = (
            db_session.query(PaperTradeModel)
            .filter(PaperTradeModel.position_id == trade.id)
            .first()
        )
        assert paper_trade is not None
        assert paper_trade.position_id == trade.id
        assert paper_trade.symbol == "SOLUSDT"
        assert paper_trade.side == "SHORT"

    def test_position_to_trade_journal(
        self, db_session, session_factory,
    ):
        signal = Signal(symbol="ADAUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        pipeline = _build_pipeline()
        executor = _build_executor(MockCollector(close_price=50000.0), session_factory)
        journal = _build_executor(MockCollector(close_price=50000.0), session_factory)
        from execution.paper import PaperExecutor as PaperDomainExecutor
        domain_executor = PaperDomainExecutor(
            position_executor=journal,
            session_factory=session_factory,
        )
        loop = ExecutionLoop(
            pipeline=pipeline,
            paper_executor=executor,
            risk_manager=RiskManager(session_factory=session_factory),
            trade_journal=domain_executor,
        )
        DecisionEngine(execution_loop=loop).process_signal(signal)

        trade = db_session.query(Trade).filter(Trade.signal_id == signal.id).first()
        assert trade is not None

        from database import PaperTrade as PaperTradeModel
        paper_trade = (
            db_session.query(PaperTradeModel)
            .filter(PaperTradeModel.position_id == trade.id)
            .first()
        )
        assert paper_trade is not None
        assert paper_trade.entry == 50000.0
        assert paper_trade.quantity > 0
        assert paper_trade.symbol == "ADAUSDT"
        assert paper_trade.side == "LONG"
        assert paper_trade.status == "OPEN"

    def test_duplicate_signal_prevention(
        self, db_session, session_factory,
    ):
        signal = Signal(symbol="DOTUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        pipeline = _build_pipeline(
            collector=MockCollector(close_price=10.0),
            scoring_engine=MockScoringEngine(),
        )
        executor = _build_executor(MockCollector(close_price=10.0), session_factory)
        journal = _build_executor(MockCollector(close_price=10.0), session_factory)
        from execution.paper import PaperExecutor as PaperDomainExecutor
        domain_executor = PaperDomainExecutor(
            position_executor=journal,
            session_factory=session_factory,
        )
        loop = ExecutionLoop(
            pipeline=pipeline,
            paper_executor=executor,
            risk_manager=RiskManager(session_factory=session_factory),
            trade_journal=domain_executor,
        )
        engine = DecisionEngine(execution_loop=loop)

        engine.process_signal(signal)
        db_session.refresh(signal)
        assert signal.status == "EXECUTED"

        first_trade = db_session.query(Trade).filter(Trade.signal_id == signal.id).first()
        assert first_trade is not None

        signal.status = "OPEN"
        db_session.flush()

        engine.process_signal(signal)
        db_session.refresh(signal)

        from database import PaperOrder as PaperOrderModel
        orders = (
            db_session.query(PaperOrderModel)
            .filter(PaperOrderModel.trade_id == first_trade.id)
            .all()
        )
        assert len(orders) == 1, "Should only have one PaperOrder despite processing signal twice"

        from database import PaperTrade as PaperTradeModel
        trades = (
            db_session.query(PaperTradeModel)
            .filter(PaperTradeModel.position_id == first_trade.id)
            .all()
        )
        assert len(trades) == 1, "Should only have one PaperTrade despite processing signal twice"
