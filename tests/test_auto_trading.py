import asyncio
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.orm import Session

from database import Signal, get_session, Trade, PaperOrder, PaperTrade
from scanner.models import Opportunity
from services.signal_generator import generate_signals_from_opportunities
from execution.execution_loop import ExecutionLoop
from execution.paper import PaperExecutor as PaperDomainExecutor
from execution.pipeline import TradeCandidate, ScoringEngine
from risk_manager import RiskManager
from config import AUTO_TRADING_ENABLED


def test_signal_generator_creates_and_deduplicates(db_session: Session):
    # Clear any leftover signals
    db_session.query(Signal).delete()
    db_session.commit()

    opps = [
        Opportunity(
            symbol="TESTUSDT",
            side="LONG",
            strategy="trend",
            score=0.85,
            confidence=85.0,
            price=100.5,
            trend_score=0.9,
            reason="Strong bullish breakout"
        ),
        Opportunity(
            symbol="TESTUSDT",
            side="LONG",
            strategy="momentum",
            score=0.95,
            confidence=95.0,
            price=101.0,
            trend_score=0.95,
            reason="Another opportunity"
        ),
        Opportunity(
            symbol="BTCUSDT",
            side="SHORT",
            strategy="reversal",
            score=0.75,
            confidence=75.0,
            price=60000.0,
            trend_score=-0.5,
            reason="Overbought mean reversion"
        )
    ]

    # First run: should create 2 signals (TESTUSDT LONG and BTCUSDT SHORT)
    created = generate_signals_from_opportunities(opps, timeframe="1h")
    assert created == 2

    # Query them back and verify fields are mapped correctly
    signals = db_session.query(Signal).all()
    assert len(signals) == 2

    test_sig = db_session.query(Signal).filter(Signal.symbol == "TESTUSDT").first()
    assert test_sig is not None
    assert test_sig.side == "LONG"
    assert test_sig.timeframe == "1h"
    assert test_sig.price == 100.5
    assert test_sig.score == 0.85
    assert test_sig.confidence == 85.0
    assert test_sig.trend_score == 0.9
    assert test_sig.status == "OPEN"
    assert test_sig.reason == "Strong bullish breakout"

    # Fields without data must stay at default
    assert test_sig.divergence is None
    assert test_sig.risk_score == 0.0

    btc_sig = db_session.query(Signal).filter(Signal.symbol == "BTCUSDT").first()
    assert btc_sig is not None
    assert btc_sig.side == "SHORT"
    assert btc_sig.price == 60000.0
    assert btc_sig.score == 0.75
    assert btc_sig.confidence == 75.0
    assert btc_sig.trend_score == -0.5
    assert btc_sig.status == "OPEN"
    assert btc_sig.reason == "Overbought mean reversion"

    # Run again with same opportunities: should skip existing OPEN signals and create 0 new signals
    created_again = generate_signals_from_opportunities(opps, timeframe="1h")
    assert created_again == 0

    # Clean up
    db_session.query(Signal).delete()
    db_session.commit()


@pytest.mark.asyncio
async def test_lifespan_background_tasks_auto_trading_conditional():
    from fastapi import FastAPI
    from api.main import lifespan, _background_tasks

    app = FastAPI()

    # Test with AUTO_TRADING_ENABLED = True
    with patch("api.main.AUTO_TRADING_ENABLED", True), \
         patch("api.main._periodic_broadcast", return_value=None), \
         patch("api.main._periodic_scan_and_signal", return_value=None), \
         patch("api.main._run_decision_engine_loop", return_value=None):
        _background_tasks.clear()
        async with lifespan(app):
            # There should be 3 background tasks registered in _background_tasks
            # 1. _periodic_broadcast
            # 2. _periodic_scan_and_signal
            # 3. _run_decision_engine_loop
            assert len(_background_tasks) == 3

    # Test with AUTO_TRADING_ENABLED = False
    with patch("api.main.AUTO_TRADING_ENABLED", False), \
         patch("api.main._periodic_broadcast", return_value=None):
        _background_tasks.clear()
        async with lifespan(app):
            # Only _periodic_broadcast should be registered
            assert len(_background_tasks) == 1


def test_execution_loop_with_trade_journal_creates_paper_objects(db_session: Session, session_factory):
    # Ensure tables are clean
    db_session.query(Trade).delete()
    db_session.query(PaperOrder).delete()
    db_session.query(PaperTrade).delete()
    db_session.query(Signal).delete()
    db_session.commit()

    # Create a Signal record
    signal = Signal(
        symbol="BTCUSDT",
        side="LONG",
        timeframe="1h",
        price=50000.0,
        score=0.9,
        confidence=90.0,
        trend_score=0.8,
        status="OPEN"
    )
    db_session.add(signal)
    db_session.commit()
    db_session.refresh(signal)

    # Initialize ExecutionLoop with a real PaperDomainExecutor as trade_journal
    # Mocking self.pipeline.evaluate to return a TradeCandidate approved
    mock_pipeline = MagicMock()
    candidate = TradeCandidate(
        id=signal.id,
        symbol=signal.symbol,
        side=signal.side,
        timeframe=signal.timeframe,
        decision="APPROVE",
        confidence=90.0,
        entry=50000.0,
        scores={"atr": 1000.0, "composite": 0.9},
        signal=signal
    )
    mock_pipeline.evaluate.return_value = candidate

    execution_loop = ExecutionLoop(
        pipeline=mock_pipeline,
        risk_manager=RiskManager(session_factory=session_factory),
        trade_journal=PaperDomainExecutor(session_factory=session_factory)
    )

    # Execute the signal through the loop
    result = execution_loop.run_once([signal])

    # Verify that a trade was successfully created
    assert result.processed == 1
    assert result.created == 1
    assert len(result.trades) == 1

    trade = result.trades[0]
    assert trade is not None
    assert trade.symbol == "BTCUSDT"
    assert trade.side == "LONG"
    assert trade.entry == 50000.0

    # Verify that a corresponding PaperOrder and PaperTrade were created
    paper_orders = db_session.query(PaperOrder).filter(PaperOrder.trade_id == trade.id).all()
    assert len(paper_orders) == 1
    assert paper_orders[0].symbol == "BTCUSDT"
    assert paper_orders[0].side == "LONG"
    assert paper_orders[0].quantity > 0.0

    paper_trades = db_session.query(PaperTrade).filter(PaperTrade.position_id == trade.id).all()
    assert len(paper_trades) == 1
    assert paper_trades[0].symbol == "BTCUSDT"
    assert paper_trades[0].side == "LONG"
    assert paper_trades[0].entry == 50000.0
    assert paper_trades[0].quantity > 0.0

    # Clean up
    db_session.query(Trade).delete()
    db_session.query(PaperOrder).delete()
    db_session.query(PaperTrade).delete()
    db_session.query(Signal).delete()
    db_session.commit()
