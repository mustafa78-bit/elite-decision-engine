from __future__ import annotations

import logging
from unittest.mock import MagicMock
import pytest

from execution.pipeline import DecisionPipeline, TradingSignal
from filters.btc_filter import BTCHealthFilter
from market_data.btc_health import BTCHealth


class MockSignal:
    def __init__(self, id: int, symbol: str, side: str, timeframe: str):
        self.id = id
        self.symbol = symbol
        self.side = side
        self.timeframe = timeframe


def test_btc_health_filter_long_healthy():
    mock_btc_health = MagicMock(spec=BTCHealth)
    mock_btc_health.score.return_value = 0.40

    filter_instance = BTCHealthFilter(btc_health=mock_btc_health)

    assert filter_instance.is_healthy() is True

    result = filter_instance.evaluate(side="LONG")
    assert result["ok"] is True
    assert result["score"] == 0.40
    assert "healthy" in result["reason"]


def test_btc_health_filter_long_unhealthy():
    mock_btc_health = MagicMock(spec=BTCHealth)
    mock_btc_health.score.return_value = 0.20

    filter_instance = BTCHealthFilter(btc_health=mock_btc_health)

    assert filter_instance.is_healthy() is False

    result = filter_instance.evaluate(side="LONG")
    assert result["ok"] is False
    assert result["score"] == 0.20
    assert "below threshold" in result["reason"]


def test_btc_health_filter_short_unhealthy():
    mock_btc_health = MagicMock(spec=BTCHealth)
    mock_btc_health.score.return_value = 0.20

    filter_instance = BTCHealthFilter(btc_health=mock_btc_health)

    result = filter_instance.evaluate(side="SHORT")
    assert result["ok"] is True
    assert result["score"] == 1.0
    assert "SHORT signals" in result["reason"]


def test_btc_health_filter_signature_inspection_dispatch():
    # Verify that DecisionPipeline._evaluate_filter successfully dispatches
    # arguments when a filter has 2 or more parameters.
    mock_btc_health = MagicMock(spec=BTCHealth)
    mock_btc_health.score.return_value = 0.20  # Unhealthy

    btc_filter = BTCHealthFilter(btc_health=mock_btc_health)
    pipeline = DecisionPipeline(filters=(btc_filter,))

    long_signal = MockSignal(id=1, symbol="ETHUSDT", side="LONG", timeframe="1h")
    short_signal = MockSignal(id=2, symbol="ETHUSDT", side="SHORT", timeframe="1h")

    # For LONG signal, the unhealthy score of 0.20 should result in rejection by filters
    assert pipeline._passes_filters(market_data=["some_data"], signal=long_signal) is False

    # For SHORT signal, even with unhealthy score of 0.20, it should bypass BTC filter and pass
    assert pipeline._passes_filters(market_data=["some_data"], signal=short_signal) is True


def test_btc_health_filter_exception_fallback():
    mock_btc_health = MagicMock(spec=BTCHealth)
    mock_btc_health.score.side_effect = Exception("API Error")

    filter_instance = BTCHealthFilter(btc_health=mock_btc_health)

    # is_healthy should handle exception and fallback to True
    assert filter_instance.is_healthy() is True

    # evaluate should handle exception and fallback to ok=True
    result = filter_instance.evaluate(side="LONG")
    assert result["ok"] is True
    assert result["score"] == 1.0
    assert "fallback" in result["reason"]
