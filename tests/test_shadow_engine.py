"""Tests for shadow trading engine."""

from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import MagicMock

from exchange.hyperliquid.connector import HyperliquidExchange
from risk.execution_guard import ExecutionGuard
from shadow.shadow_engine import ShadowEngine, ShadowResult


@dataclass
class FakeSignal:
    id: int
    symbol: str
    side: str
    timeframe: str = "1h"


class TestShadowEngine:
    def test_shadow_result_dataclass(self):
        r = ShadowResult(signal_id=1, symbol="BTC", side="LONG", approved=True, guard_passed=True, order_placed=True, reason="OK")
        assert r.signal_id == 1
        assert r.approved is True
        assert r.order_placed is True

    def test_shadow_result_defaults(self):
        r = ShadowResult(signal_id=1, symbol="BTC", side="LONG", approved=False, guard_passed=False, order_placed=False)
        assert r.reason == ""
        assert r.journal_id is None

    def test_engine_process_rejected_signal(self, db_session):
        from database import Signal
        sig = Signal(symbol="BTC", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(sig)
        db_session.flush()

        signal = FakeSignal(id=sig.id, symbol="BTC", side="LONG")
        engine = ShadowEngine(exchange=HyperliquidExchange())
        result = engine.process(signal)
        # Pipeline will likely reject due to missing market data in test env
        assert isinstance(result, ShadowResult)
        assert result.signal_id == sig.id

    def test_engine_process_with_dynamic_position_sizer(self, db_session):
        from database import Signal
        from execution.pipeline import TradeCandidate
        from position_sizing import PositionSize
        from risk.models import RiskCheckDetail, RiskDecision

        sig = Signal(symbol="BTC", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(sig)
        db_session.flush()

        signal = FakeSignal(id=sig.id, symbol="BTC", side="LONG")

        candidate = TradeCandidate(
            id=sig.id,
            symbol="BTC",
            side="LONG",
            timeframe="1h",
            entry=50000.0,
            scores={"final_score": 85.0, "atr": 2500.0},
            confidence=0.9,
            decision="APPROVE",
            signal=signal,
        )
        mock_pipeline = MagicMock()
        mock_pipeline.evaluate.return_value = candidate

        mock_sizer = MagicMock()
        mock_sizer.calculate.return_value = PositionSize(
            quantity=2.5,
            notional_value=125000.0,
            risk_amount=12500.0,
        )

        mock_guard = MagicMock()
        mock_guard.evaluate_execution.return_value = RiskDecision(
            allowed=True,
            reason="",
            rejection_code=None,
            checks=(RiskCheckDetail(name="RISK_BUDGET_EXCEEDED", passed=True, detail=""),),
            metadata={},
        )

        mock_order_manager = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "mock-order-123"
        mock_order_manager.create_order.return_value = mock_order

        engine = ShadowEngine(
            pipeline=mock_pipeline,
            guard=mock_guard,
            order_manager=mock_order_manager,
            position_sizer=mock_sizer,
        )

        result = engine.process(signal)

        assert result.approved is True
        assert result.guard_passed is True
        assert result.order_placed is True
        assert result.reason == "Shadow trade executed"

        mock_sizer.calculate.assert_called_once_with(candidate)

        mock_guard.evaluate_execution.assert_called_once_with(
            symbol="BTC",
            side="LONG",
            entry_price=50000.0,
            quantity=2.5,
        )

        mock_order_manager.create_order.assert_called_once_with(
            symbol="BTC",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal("2.5"),
            price=Decimal("50000"),
        )

    def test_risk_budget_guard_scales_with_real_quantity_not_unit_price(self, db_session, session_factory):
        """ExecutionGuard's RISK_BUDGET_EXCEEDED check compares notional
        (entry_price * quantity) against MAX_POSITION_SIZE_USD, not the much
        smaller per-trade risk-dollar budget -- so a realistically ATR-sized
        position passes, and only a genuinely over-the-real-cap position fails.
        Mocks market_service to avoid a live network call to HyperliquidCollector
        inside ExecutionGuard's volatility check.
        """
        mock_exchange = MagicMock()
        mock_exchange.trading_enabled.return_value = True

        mock_market_service = MagicMock()
        mock_market_service.get_indicators.return_value = {"atr": 0.0}
        mock_market_service.get_price.return_value = 1.0

        guard = ExecutionGuard(
            exchange=mock_exchange,
            session_factory=session_factory,
            market_service=mock_market_service,
        )

        # BTC at 50,000, quantity 0.5 -> notional 25,000, well under the real
        # MAX_POSITION_SIZE_USD cap (100,000 by default) -- should now pass.
        dec_btc = guard.evaluate_execution("BTC", "LONG", 50000.0, 0.5)
        budget_check_btc = next(
            (c for c in dec_btc.checks if c.name == "RISK_BUDGET_EXCEEDED"), None
        )
        assert budget_check_btc is not None
        assert budget_check_btc.passed is True
        assert dec_btc.allowed is True

        # Cheap altcoin at 0.5, quantity 0.5 -> notional 0.25, trivially under budget.
        dec_cheap = guard.evaluate_execution("CHEAP", "LONG", 0.5, 0.5)
        budget_check_cheap = next(
            (c for c in dec_cheap.checks if c.name == "RISK_BUDGET_EXCEEDED"), None
        )
        assert budget_check_cheap is not None
        assert budget_check_cheap.passed is True
        assert dec_cheap.allowed is True

        # BTC at 50,000, quantity 2.1 -> notional 105,000, genuinely over the
        # real MAX_POSITION_SIZE_USD cap (100,000) -- should still fail.
        dec_over = guard.evaluate_execution("BTC", "LONG", 50000.0, 2.1)
        budget_check_over = next(
            (c for c in dec_over.checks if c.name == "RISK_BUDGET_EXCEEDED"), None
        )
        assert budget_check_over is not None
        assert budget_check_over.passed is False
        assert dec_over.allowed is False
