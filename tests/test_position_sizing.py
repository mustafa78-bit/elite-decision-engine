"""Unit tests for the PositionSizingEngine — covers all sizing scenarios."""

import pytest
from position_sizing import PositionSizingEngine, PositionSize


class _MockCandidate:
    def __init__(self, entry: float, atr: float):
        self.entry = entry
        self.scores = {"atr": atr}


class TestPositionSizing:

    def test_normal_account(self):
        sizer = PositionSizingEngine(
            account_equity=10000,
            risk_percentage=1.0,
            atr_multiplier=1.5,
            max_position_usd=100000,
            min_quantity=0.001,
        )
        result = sizer.calculate(_MockCandidate(entry=50000.0, atr=500.0))
        assert isinstance(result, PositionSize)
        assert result.quantity == pytest.approx(0.13333333, abs=1e-8)
        assert result.notional_value == pytest.approx(6666.67, abs=0.01)
        assert result.risk_amount == pytest.approx(100.0, abs=0.01)

    def test_small_account(self):
        sizer = PositionSizingEngine(
            account_equity=500,
            risk_percentage=1.0,
            atr_multiplier=1.5,
        )
        result = sizer.calculate(_MockCandidate(entry=50000.0, atr=500.0))
        assert result.quantity == pytest.approx(0.00666667, abs=1e-8)
        assert result.notional_value == pytest.approx(333.33, abs=0.01)
        assert result.risk_amount == pytest.approx(5.0, abs=0.01)

    def test_large_account_caps_notional(self):
        sizer = PositionSizingEngine(
            account_equity=1_000_000,
            risk_percentage=1.0,
            atr_multiplier=1.5,
            max_position_usd=100000,
            min_quantity=0.001,
        )
        result = sizer.calculate(_MockCandidate(entry=50000.0, atr=500.0))
        assert result.quantity == pytest.approx(2.0, abs=1e-8)
        assert result.notional_value == pytest.approx(100000.0, abs=0.01)
        assert result.risk_amount == pytest.approx(1500.0, abs=0.01)

    def test_high_atr_smaller_position(self):
        sizer = PositionSizingEngine(
            account_equity=10000,
            risk_percentage=1.0,
            atr_multiplier=1.5,
        )
        result = sizer.calculate(_MockCandidate(entry=50000.0, atr=5000.0))
        assert result.quantity == pytest.approx(0.01333333, abs=1e-8)
        assert result.notional_value == pytest.approx(666.67, abs=0.01)
        assert result.risk_amount == pytest.approx(100.0, abs=0.01)

    def test_low_atr_larger_position(self):
        sizer = PositionSizingEngine(
            account_equity=10000,
            risk_percentage=1.0,
            atr_multiplier=1.5,
        )
        result = sizer.calculate(_MockCandidate(entry=50000.0, atr=50.0))
        assert result.quantity == pytest.approx(1.33333333, abs=1e-8)
        assert result.notional_value == pytest.approx(66666.67, abs=0.01)
        assert result.risk_amount == pytest.approx(100.0, abs=0.01)

    def test_minimum_quantity_floor(self):
        sizer = PositionSizingEngine(
            account_equity=100,
            risk_percentage=1.0,
            atr_multiplier=1.5,
            min_quantity=0.001,
        )
        result = sizer.calculate(_MockCandidate(entry=50000.0, atr=5000.0))
        assert result.quantity == 0.001
        assert result.notional_value == pytest.approx(50.0, abs=0.01)
        assert result.risk_amount == pytest.approx(7.5, abs=0.01)

    def test_zero_atr_uses_minimum(self):
        sizer = PositionSizingEngine(
            account_equity=10000,
            risk_percentage=1.0,
            atr_multiplier=1.5,
            min_quantity=0.001,
        )
        result = sizer.calculate(_MockCandidate(entry=50000.0, atr=0.0))
        assert result.quantity == 0.001
        assert result.notional_value == pytest.approx(50.0, abs=0.01)
        assert result.risk_amount == 0.0
