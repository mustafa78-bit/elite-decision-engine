from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from database import Signal, Trade, EventLedger
from core.ledger import LedgerService
from core.kernel import DecisionKernel
from core.trust import TrustMetricsService
from core.timeline import FounderTimelineService
from services.ollo.ollo_service import OLLOService


def test_event_ledger_append_and_query(db_session, session_factory):
    """Test append-only event ledger operations."""
    ledger = LedgerService(session_factory=session_factory)

    # 1. Append Signal Created
    event = ledger.append_event(
        event_type="Signal Created",
        symbol="BTCUSDT",
        signal_id=100,
        description="BTC signal created",
        details={"score": 90.0, "timeframe": "1h"},
    )
    assert event.id is not None
    assert event.event_type == "Signal Created"
    assert event.symbol == "BTCUSDT"
    assert event.signal_id == 100
    assert event.details["score"] == 90.0

    # Query all events
    events = ledger.get_events()
    assert len(events) >= 1
    assert events[0].event_type == "Signal Created"

    # Query signal-specific events
    sig_events = ledger.get_signal_events(100)
    assert len(sig_events) == 1
    assert sig_events[0].event_type == "Signal Created"


def test_decision_kernel_orchestration(db_session, session_factory):
    """Test central decision kernel orchestration, logging, and learning hooks."""
    ledger = LedgerService(session_factory=session_factory)

    # Setup mocks for pipeline, risk, sizing, trade engine
    mock_pipeline = MagicMock()
    mock_risk = MagicMock()
    mock_sizer = MagicMock()
    mock_engine = MagicMock()

    signal = Signal(id=50, symbol="ETHUSDT", side="LONG", timeframe="1h")

    from execution.pipeline import TradeCandidate
    candidate = TradeCandidate(
        id=50, symbol="ETHUSDT", side="LONG", timeframe="1h",
        entry=3000.0, scores={"atr": 100.0}, confidence=85.0,
        decision="APPROVE", signal=signal,
    )
    mock_pipeline.evaluate.return_value = candidate

    class MockRiskDecision:
        allowed = True
        rejection_code = None
        reason = None
    mock_risk.evaluate_trade.return_value = MockRiskDecision()

    class MockPositionSize:
        quantity = 1.5
        notional_value = 4500.0
        risk_amount = 150.0
    mock_sizer.calculate.return_value = MockPositionSize()

    mock_trade = Trade(id=101, signal_id=50, symbol="ETHUSDT", side="LONG", entry=3000.0, stop=2900.0, tp1=3100.0)
    mock_engine.create_trade.return_value = mock_trade

    kernel = DecisionKernel(
        ledger_service=ledger,
        pipeline=mock_pipeline,
        risk_manager=mock_risk,
        position_sizer=mock_sizer,
        trade_engine=mock_engine,
    )

    trade = kernel.evaluate_and_execute_signal(signal)
    assert trade is not None
    assert trade.id == 101

    # Verify ledger entries (Signal Created -> Decision Generated -> Risk Evaluation -> Trade Executed -> Feedback Stored)
    sig_events = ledger.get_signal_events(50)
    event_types = [e.event_type for e in sig_events]
    assert "Signal Created" in event_types
    assert "Decision Generated" in event_types
    assert "Risk Evaluation" in event_types
    assert "Trade Executed" in event_types
    assert "Feedback Stored" in event_types


def test_trust_metrics_calculation(db_session, session_factory):
    """Test Trust Metrics derived directly from the Ledger."""
    ledger = LedgerService(session_factory=session_factory)

    # Log completed trade outcome events directly into the Ledger
    ledger.append_event(
        event_type="Decision Generated", symbol="SOLUSDT", signal_id=1,
        details={"confidence": 90.0},
    )
    ledger.append_event(
        event_type="Outcome Calculated", symbol="SOLUSDT", signal_id=1, trade_id=201,
        details={"success": True, "pnl": 500.0},
    )
    ledger.append_event(
        event_type="Feedback Stored", symbol="SOLUSDT", signal_id=1, trade_id=201,
        details={"stage": "CLOSURE", "reason_for_success": "TP_HIT"},
    )

    ledger.append_event(
        event_type="Decision Generated", symbol="SOLUSDT", signal_id=2,
        details={"confidence": 85.0},
    )
    ledger.append_event(
        event_type="Outcome Calculated", symbol="SOLUSDT", signal_id=2, trade_id=202,
        details={"success": False, "pnl": -200.0},
    )
    ledger.append_event(
        event_type="Feedback Stored", symbol="SOLUSDT", signal_id=2, trade_id=202,
        details={"stage": "CLOSURE", "reason_for_failure": "SL_HIT"},
    )

    service = TrustMetricsService(session_factory=session_factory)
    metrics = service.calculate_metrics()

    assert metrics["total_trades"] == 2
    assert metrics["win_rate"] == 50.0
    assert metrics["loss_rate"] == 50.0
    assert metrics["average_return"] == 150.0
    assert metrics["trust_score"] > 0
    assert "TP_HIT" in metrics["reasons_for_success"]
    assert "SL_HIT" in metrics["reasons_for_failure"]


def test_founder_timeline_narrative(db_session, session_factory):
    """Test Founder Timeline chronological narrative stories projection."""
    ledger = LedgerService(session_factory=session_factory)

    # 4-phase sequence for a signal
    ledger.append_event(
        event_type="Signal Created", symbol="AVAXUSDT", signal_id=5,
        description="AVAX breakout signal", details={"price": 30.0},
    )
    ledger.append_event(
        event_type="Decision Generated", symbol="AVAXUSDT", signal_id=5,
        description="Decision STRONG_APPROVE with 95% confidence", details={"decision": "STRONG_APPROVE", "confidence": 95.0},
    )
    ledger.append_event(
        event_type="Trade Executed", symbol="AVAXUSDT", signal_id=5, trade_id=505,
        description="Trade executed", details={"entry_price": 30.0},
    )
    ledger.append_event(
        event_type="Outcome Calculated", symbol="AVAXUSDT", signal_id=5, trade_id=505,
        description="Outcome SUCCESS with PnL +150", details={"pnl": 150.0, "success": True},
    )

    service = FounderTimelineService(session_factory=session_factory)
    timeline = service.get_founder_timeline()

    assert len(timeline) >= 1
    story = timeline[0]
    assert story["symbol"] == "AVAXUSDT"
    assert story["analyzed"]["description"] == "AVAX breakout signal"
    assert story["decision_made"]["decision"] == "STRONG_APPROVE"
    assert story["action_followed"]["description"] == "Trade executed"
    assert story["afterwards"]["description"] == "Outcome SUCCESS with PnL +150"


def test_ollo_tool_layer_actions():
    """Test upgraded OLLO Tool Layer parses and maps queries to structured action payloads."""
    mock_ai = MagicMock()
    mock_chat_response = MagicMock()
    mock_chat_response.content = "Sure, opening the portfolio workstation."
    mock_chat_response.provider = "test"
    mock_chat_response.model = "test"
    mock_chat_response.tokens_in = 10
    mock_chat_response.tokens_out = 20
    mock_chat_response.retries = 0
    mock_ai.chat.return_value = mock_chat_response

    svc = OLLOService(ai_service=mock_ai)

    # Test open portfolio query
    resp = svc.query("Please open the portfolio page.")
    assert resp.action_executed is not None
    assert resp.action_executed["action"] == "open_portfolio"
    assert resp.action_executed["status"] == "executed"

    # Test analyze btc query
    resp = svc.query("Can you analyze btc for me?")
    assert resp.action_executed is not None
    assert resp.action_executed["action"] == "analyze_btc"
    assert resp.action_executed["status"] == "executed"
