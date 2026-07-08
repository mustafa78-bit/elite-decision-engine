"""Tests for execution risk guard."""

import pytest

from exchange.hyperliquid.connector import HyperliquidExchange
from risk.execution_guard import ExecutionGuard, GuardResult


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
