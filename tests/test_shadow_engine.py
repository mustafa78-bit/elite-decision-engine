"""Tests for shadow trading engine."""

from dataclasses import dataclass

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
        r = ShadowResult(
            signal_id=1,
            symbol="BTC",
            side="LONG",
            approved=True,
            guard_passed=True,
            order_placed=True,
            reason="OK"
        )
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

    def test_engine_process_with_dynamic_position_sizer(self, db_session, mocker):
        from database import Signal
        from execution.pipeline import TradeCandidate
        from position_sizing import PositionSize, PositionSizingEngine
        from risk.models import RiskCheckDetail, RiskDecision

        # Seed signal
        sig = Signal(symbol="BTC", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(sig)
        db_session.flush()

        signal = FakeSignal(id=sig.id, symbol="BTC", side="LONG")

        # Mock decision pipeline to approve
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
        mock_pipeline = mocker.MagicMock()
        mock_pipeline.evaluate.return_value = candidate

        # Mock position sizing engine to return a specific non-trivial quantity
        mock_sizer = mocker.MagicMock(spec=PositionSizingEngine)
        mock_sizer.calculate.return_value = PositionSize(
            quantity=2.5,
            notional_value=125000.0,
            risk_amount=12500.0,
        )

        # Mock execution guard to pass
        mock_guard = mocker.MagicMock()
        mock_guard.evaluate_execution.return_value = RiskDecision(
            allowed=True,
            reason="Passed",
            rejection_code=None,
            checks=[
                RiskCheckDetail(name="RISK_BUDGET_EXCEEDED", passed=True, detail="")
            ],
            metadata={},
        )

        # Mock order manager to succeed
        mock_order_manager = mocker.MagicMock()
        mock_order = mocker.MagicMock()
        mock_order.id = "mock-order-123"
        mock_order_manager.create_order.return_value = mock_order

        # Create engine with injected mocks
        engine = ShadowEngine(
            pipeline=mock_pipeline,
            guard=mock_guard,
            order_manager=mock_order_manager,
            position_sizer=mock_sizer,
        )

        # Run process
        result = engine.process(signal)

        # Assertions
        assert result.approved is True
        assert result.guard_passed is True
        assert result.order_placed is True
        assert result.reason == "Shadow trade executed"

        # Check PositionSizingEngine is called with the candidate
        mock_sizer.calculate.assert_called_once_with(candidate)

        # Check ExecutionGuard is called with the dynamic quantity
        mock_guard.evaluate_execution.assert_called_once_with(
            symbol="BTC",
            side="LONG",
            entry_price=50000.0,
            quantity=2.5,
        )

        # Check OrderManager is called with the dynamic Decimal quantity
        from decimal import Decimal
        mock_order_manager.create_order.assert_called_once_with(
            symbol="BTC",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal("2.5"),
            price=Decimal("50000"),
        )

    def test_risk_budget_guard_with_high_vs_low_priced_assets(self, db_session, session_factory, mocker):
        from exchange.base import ExchangeAdapter

        # High priced BTC vs Cheap altcoin
        # Mock exchange adapter to return online
        mock_exchange = mocker.MagicMock(spec=ExchangeAdapter)
        mock_exchange.trading_enabled.return_value = True

        # Using a real execution guard to see how the risk budget check behaves
        # Let's override the ACCOUNT_EQUITY and RISK_PER_TRADE_PERCENT dynamically
        # if possible, or use config values. By default in config.py,
        # ACCOUNT_EQUITY = 100000.0 and RISK_PER_TRADE_PERCENT = 1.0 (so max_notional is 1000.0)
        # We can mock config constants if needed, or work with default limits.
        # Let's set up quantities that exceed and stay within the budget.

        # Scenario A: High priced BTC at 50,000. Quantity 0.5 -> notional is 25,000. Exceeds risk budget of 1,000.
        # Scenario B: Cheap altcoin at 0.5. Quantity 0.5 -> notional is 0.25. Under risk budget.

        # Let's check with ExecutionGuard directly first, or via ShadowEngine.
        guard = ExecutionGuard(exchange=mock_exchange, session_factory=session_factory)

        # Scenario A (BTC, 50,000, qty 0.5 -> 25,000)
        dec_btc = guard.evaluate_execution("BTC", "LONG", 50000.0, 0.5)
        # Should fail RISK_BUDGET_EXCEEDED
        budget_check_btc = next((c for c in dec_btc.checks if c.name == "RISK_BUDGET_EXCEEDED"), None)
        assert budget_check_btc is not None
        assert budget_check_btc.passed is False
        assert dec_btc.allowed is False

        # Scenario B (CHEAP, 0.5, qty 0.5 -> 0.25)
        # Note: Volatility check might look up OHLCV data. Let's mock the collector
        # or market_service on guard to avoid live calls.
        mock_market_service = mocker.MagicMock()
        mock_market_service.get_indicators.return_value = {"atr": 0.01}
        mock_market_service.get_price.return_value = 0.5
        guard.market_service = mock_market_service

        dec_cheap = guard.evaluate_execution("CHEAP", "LONG", 0.5, 0.5)
        # Should pass RISK_BUDGET_EXCEEDED (0.25 <= 1000.0)
        budget_check_cheap = next((c for c in dec_cheap.checks if c.name == "RISK_BUDGET_EXCEEDED"), None)
        assert budget_check_cheap is not None
        assert budget_check_cheap.passed is True
