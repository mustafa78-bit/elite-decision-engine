"""Tests for execution risk guard."""

import pytest

from exchange.hyperliquid.connector import HyperliquidExchange
from risk.execution_guard import ExecutionGuard, GuardResult
from risk.models import RiskDecision


class TestExecutionGuard:
    def test_requires_exchange(self):
        guard = ExecutionGuard(exchange=None)
        result = guard.can_execute(symbol="BTC", side="LONG", entry_price=50000.0, quantity=1.0)
        assert result.allowed is False
        assert "No exchange configured" in result.reason

    def test_estimate_position_size(self):
        guard = ExecutionGuard(exchange=HyperliquidExchange())
        size = guard.estimate_position_size(entry_price=50000.0, stop_price=49000.0, account_equity=10000.0)
        # 1% of 10000 = 100, price risk = 1000, so size = 0.1
        assert size == pytest.approx(0.1, rel=0.01)

    def test_estimate_position_size_zero_risk(self):
        guard = ExecutionGuard(exchange=HyperliquidExchange())
        size = guard.estimate_position_size(entry_price=50000.0, stop_price=50000.0)
        assert size == 0.0

    def test_guard_result_dataclass(self):
        result = GuardResult(allowed=True, reason="", checks={"test": True})
        assert result.allowed is True
        assert result.reason == ""
        assert result.checks["test"] is True

    def test_guard_result_failure(self):
        result = GuardResult(allowed=False, reason="Test failure", checks={"test": False})
        assert result.allowed is False
        assert "Test failure" in result.reason


class TestExecutionGuardEvaluate:

    def test_evaluate_execution_no_exchange(self):
        guard = ExecutionGuard(exchange=None)
        decision = guard.evaluate_execution(
            symbol="BTC", side="LONG", entry_price=50000.0, quantity=1.0,
        )
        assert isinstance(decision, RiskDecision)
        assert decision.allowed is False
        assert decision.rejection_code == "EXCHANGE_NOT_CONFIGURED"

    def test_evaluate_execution_returns_all_checks_on_success(self, session_factory):
        guard = ExecutionGuard(exchange=HyperliquidExchange(), session_factory=session_factory)
        decision = guard.evaluate_execution(
            symbol="BTC", side="LONG", entry_price=50000.0, quantity=0.001,
        )
        check_names = {c.name for c in decision.checks}
        assert "EXCHANGE_OFFLINE" in check_names
        assert "MAX_OPEN_TRADES" in check_names

    def test_evaluate_execution_includes_metadata(self, session_factory):
        guard = ExecutionGuard(exchange=HyperliquidExchange(), session_factory=session_factory)
        decision = guard.evaluate_execution(
            symbol="BTC", side="LONG", entry_price=50000.0, quantity=0.001,
        )
        assert "volatility_pct" in decision.metadata or "regime" in decision.metadata

    def test_backward_compat_can_execute_still_works(self):
        guard = ExecutionGuard(exchange=None)
        result = guard.can_execute(symbol="BTC", side="LONG", entry_price=50000.0, quantity=1.0)
        assert isinstance(result, GuardResult)
        assert result.allowed is False
        assert "No exchange configured" in result.reason

    def test_backward_compat_guard_result_fields(self, session_factory):
        guard = ExecutionGuard(exchange=HyperliquidExchange(), session_factory=session_factory)
        result = guard.can_execute(symbol="BTC", side="LONG", entry_price=50000.0, quantity=0.001)
        assert "EXCHANGE_OFFLINE" in result.checks or "exchange_online" in result.checks

    def test_risk_budget_guard_scales_with_real_quantity_not_unit_price(self, session_factory):
        # With default config: ACCOUNT_EQUITY=10000, RISK_PER_TRADE_PERCENT=1.0, MAX_POSITION_SIZE_USD=100000
        # A realistically-sized position: BTC at 50,000, quantity 0.5 (notional = $25,000)
        # Old code compared $25,000 against a $100 "budget" limit and failed.
        # Fixed code compares $25,000 against $100,000 limit and should pass.
        guard = ExecutionGuard(exchange=HyperliquidExchange(), session_factory=session_factory)
        decision = guard.evaluate_execution(
            symbol="BTC", side="LONG", entry_price=50000.0, quantity=0.5,
        )
        assert decision.allowed is True

        # Verify specific RISK_BUDGET_EXCEEDED check passed
        budget_check = next(c for c in decision.checks if c.name == "RISK_BUDGET_EXCEEDED")
        assert budget_check.passed is True
        assert budget_check.value == 25000.0
        assert budget_check.limit == 100000.0

    def test_risk_budget_guard_fails_on_genuine_over_budget(self, session_factory):
        # A position exceeding MAX_POSITION_SIZE_USD: BTC at 50,000, quantity 2.1 (notional = $105,000)
        guard = ExecutionGuard(exchange=HyperliquidExchange(), session_factory=session_factory)
        decision = guard.evaluate_execution(
            symbol="BTC", side="LONG", entry_price=50000.0, quantity=2.1,
        )
        assert decision.allowed is False

        budget_check = next(c for c in decision.checks if c.name == "RISK_BUDGET_EXCEEDED")
        assert budget_check.passed is False
        assert "exceeds max position size limit" in budget_check.detail
        assert budget_check.value == 105000.0
        assert budget_check.limit == 100000.0
