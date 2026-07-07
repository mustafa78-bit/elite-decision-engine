"""Deterministic unit tests for LiveExecutor and ExecutionRouter.

All external dependencies are mocked or use built-in simulated adapters.
No internet, no API, no secrets, no exchange calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from unittest.mock import MagicMock

from execution.hyperliquid_adapter import HyperliquidReadOnlyAdapter, Position
from execution.live_executor import (
    LiveExecutor,
    LiveMonitorResult,
    LiveOrderResult,
    SimulatedExchangeAdapter,
)
from execution.router import ExecutionRouter, TradingMode
from position_sizing import PositionSize


@dataclass(frozen=True)
class _MockTrade:
    id: int = 99


class _MockPaperExecutor:
    """Mock PaperExecutor that never touches the database."""

    def __init__(self):
        self.calls = []

    def open_trade(self, **kwargs):
        self.calls.append(kwargs)
        return _MockTrade(id=42)

    def monitor_open_trades(self):
        return []


@dataclass(frozen=True)
class _MockCandidate:
    id: int = 1
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    timeframe: str = "1h"
    entry: float = 50000.0
    scores: dict = None
    confidence: float = 0.9
    decision: str = "APPROVE"
    signal: Any = None

    def __post_init__(self):
        if self.scores is None:
            object.__setattr__(self, "scores", {"atr": 500.0})


class _MockHyperliquidAdapter:
    """Mock read-only adapter that returns canned data."""

    def __init__(self):
        self.get_positions_calls = 0
        self.get_open_orders_calls = 0
        self.get_current_prices_calls = 0

    def get_positions(self, address: str) -> list:
        self.get_positions_calls += 1
        return [
            Position(
                coin="BTC",
                size=0.5,
                entry_px=50000.0,
                unrealized_pnl=250.0,
                liquidation_px=45000.0,
            ),
        ]

    def get_open_orders(self, address: str) -> list:
        self.get_open_orders_calls += 1
        from execution.hyperliquid_adapter import OpenOrder
        return [
            OpenOrder(coin="BTC", side="B", limit_px=49000.0, sz=0.1, order_id=12345, status="open"),
        ]

    def get_current_prices(self) -> dict[str, float]:
        self.get_current_prices_calls += 1
        return {"BTC": 50250.0, "ETH": 3000.0}


class _MockHyperliquidAdapterEmpty:
    """Mock adapter that returns no positions."""

    def get_positions(self, address: str) -> list:
        return []

    def get_open_orders(self, address: str) -> list:
        return []

    def get_current_prices(self) -> dict[str, float]:
        return {}


class _MockHyperliquidAdapterError:
    """Mock adapter that raises on any call."""

    def get_positions(self, address: str) -> list:
        raise RuntimeError("API error")

    def get_open_orders(self, address: str) -> list:
        raise RuntimeError("API error")

    def get_current_prices(self) -> dict[str, float]:
        raise RuntimeError("API error")


class _MockExchangeAdapter:
    """Deterministic adapter for testing."""

    def __init__(self):
        self.place_order_calls: list[dict] = []

    def place_order(self, payload: dict) -> dict:
        self.place_order_calls.append(payload)
        return {"order_id": "test-order-123", "status": "NEW", "filled": 0.0}

    def cancel_order(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "CANCELED"}

    def get_order_status(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "FILLED", "filled": 1.0}


_SIZE_1 = PositionSize(quantity=1.0, notional_value=50000.0, risk_amount=750.0)
_SIZE_0 = PositionSize(quantity=0.0, notional_value=0.0, risk_amount=0.0)


class TestSimulatedExchangeAdapter:

    def test_place_order_returns_canned_response(self):
        adapter = SimulatedExchangeAdapter()
        result = adapter.place_order({"symbol": "BTCUSDT"})
        assert result["status"] == "NEW"
        assert "order_id" in result
        assert result["filled"] == 0.0

    def test_cancel_order_returns_canceled(self):
        adapter = SimulatedExchangeAdapter()
        result = adapter.cancel_order("order-1")
        assert result["status"] == "CANCELED"

    def test_get_order_status_returns_filled(self):
        adapter = SimulatedExchangeAdapter()
        result = adapter.get_order_status("order-1")
        assert result["status"] == "FILLED"


class TestLiveExecutor:

    def test_execute_valid_trade_returns_accepted(self):
        executor = LiveExecutor(exchange_adapter=_MockExchangeAdapter())
        result = executor.execute(_MockCandidate(), _SIZE_1)
        assert result.accepted is True
        assert result.mode == "LIVE"
        assert result.exchange == "Hyperliquid"
        assert result.client_order_id == "test-order-123"
        assert result.error is None

    def test_execute_rejected_when_candidate_is_none(self):
        executor = LiveExecutor()
        result = executor.execute(None, _SIZE_1)
        assert result.accepted is False
        assert result.error is not None

    def test_execute_rejected_when_size_is_none(self):
        executor = LiveExecutor()
        result = executor.execute(_MockCandidate(), None)
        assert result.accepted is False
        assert result.error is not None

    def test_execute_rejected_for_bad_side(self):
        candidate = _MockCandidate(side="INVALID")
        executor = LiveExecutor()
        result = executor.execute(candidate, _SIZE_1)
        assert result.accepted is False
        assert "side must be LONG or SHORT" in result.error

    def test_execute_rejected_for_zero_entry(self):
        candidate = _MockCandidate(entry=0.0)
        executor = LiveExecutor()
        result = executor.execute(candidate, _SIZE_1)
        assert result.accepted is False
        assert "entry must be greater than zero" in result.error

    def test_execute_rejected_for_zero_quantity(self):
        executor = LiveExecutor()
        result = executor.execute(_MockCandidate(), _SIZE_0)
        assert result.accepted is False
        assert "quantity must be greater than zero" in result.error

    def test_execute_payload_contains_correct_fields(self):
        adapter = _MockExchangeAdapter()
        executor = LiveExecutor(exchange_adapter=adapter)
        executor.execute(_MockCandidate(symbol="ETHUSDT", side="SHORT", entry=3000.0), _SIZE_1)
        assert len(adapter.place_order_calls) == 1
        payload = adapter.place_order_calls[0]
        assert payload["symbol"] == "ETHUSDT"
        assert payload["side"] == "SHORT"
        assert payload["price"] == 3000.0
        assert payload["quantity"] == 1.0
        assert payload["order_type"] == "LIMIT"

    def test_payload_contains_signature_placeholder(self):
        adapter = _MockExchangeAdapter()
        executor = LiveExecutor(exchange_adapter=adapter)
        executor.execute(_MockCandidate(), _SIZE_1)
        payload = adapter.place_order_calls[0]
        assert "SIMULATED_SIGNATURE_PLACEHOLDER" in str(payload.get("signature", ""))

    def test_payload_contains_timestamp(self):
        adapter = _MockExchangeAdapter()
        executor = LiveExecutor(exchange_adapter=adapter)
        executor.execute(_MockCandidate(), _SIZE_1)
        payload = adapter.place_order_calls[0]
        assert "signing_timestamp" in payload
        assert "timestamp" in payload

    def test_monitor_open_trades_returns_empty_list(self):
        executor = LiveExecutor()
        results = executor.monitor_open_trades()
        assert results == []

    def test_execute_uses_custom_exchange_adapter(self):
        adapter = _MockExchangeAdapter()
        executor = LiveExecutor(exchange_adapter=adapter)
        executor.execute(_MockCandidate(), _SIZE_1)
        assert len(adapter.place_order_calls) == 1

    def test_live_order_result_dataclass(self):
        result = LiveOrderResult(
            accepted=True,
            client_order_id="oid-1",
            payload={"key": "val"},
            response={"status": "NEW"},
        )
        assert result.accepted is True
        assert result.mode == "LIVE"
        assert result.client_order_id == "oid-1"
        assert result.payload["key"] == "val"
        assert result.response["status"] == "NEW"

    def test_rejected_live_order_result(self):
        result = LiveOrderResult(accepted=False, error="test error")
        assert result.accepted is False
        assert result.error == "test error"

    def test_monitor_with_adapter_returns_live_monitor_results(self):
        adapter = _MockHyperliquidAdapter()
        executor = LiveExecutor(
            hyperliquid_adapter=adapter,
            address="0xABC",
        )
        results = executor.monitor_open_trades()
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, LiveMonitorResult)
        assert r.symbol == "BTCUSDT"
        assert r.side == "LONG"
        assert r.size == 0.5
        assert r.entry_price == 50000.0
        assert r.mark_price == 50250.0
        assert r.unrealized_pnl == 250.0
        assert r.liquidation_price == 45000.0
        assert r.order_status == "open"
        assert r.exchange_order_id == "12345"

    def test_monitor_calls_adapter_methods(self):
        adapter = _MockHyperliquidAdapter()
        executor = LiveExecutor(hyperliquid_adapter=adapter, address="0xABC")
        executor.monitor_open_trades()
        assert adapter.get_positions_calls == 1
        assert adapter.get_open_orders_calls == 1
        assert adapter.get_current_prices_calls == 1

    def test_monitor_empty_positions_returns_empty_list(self):
        adapter = _MockHyperliquidAdapterEmpty()
        executor = LiveExecutor(hyperliquid_adapter=adapter, address="0xABC")
        results = executor.monitor_open_trades()
        assert results == []

    def test_monitor_no_address_returns_empty_list(self):
        executor = LiveExecutor(hyperliquid_adapter=_MockHyperliquidAdapter())
        results = executor.monitor_open_trades()
        assert results == []

    def test_monitor_no_adapter_returns_empty_list(self):
        executor = LiveExecutor()
        results = executor.monitor_open_trades()
        assert results == []

    def test_monitor_adapter_error_returns_empty_list(self):
        adapter = _MockHyperliquidAdapterError()
        executor = LiveExecutor(hyperliquid_adapter=adapter, address="0xABC")
        results = executor.monitor_open_trades()
        assert results == []

    def test_monitor_short_position_side(self):
        adapter = _MockHyperliquidAdapter()
        adapter.get_positions = lambda addr: [
            Position(coin="ETH", size=-2.0, entry_px=3000.0, unrealized_pnl=-100.0, liquidation_px=3200.0),
        ]
        executor = LiveExecutor(hyperliquid_adapter=adapter, address="0xABC")
        results = executor.monitor_open_trades()
        assert len(results) == 1
        assert results[0].side == "SHORT"

    def test_monitor_uses_mark_price_from_prices(self):
        adapter = _MockHyperliquidAdapter()
        adapter.get_current_prices = lambda: {"BTC": 51000.0}
        executor = LiveExecutor(hyperliquid_adapter=adapter, address="0xABC")
        results = executor.monitor_open_trades()
        assert results[0].mark_price == 51000.0

    def test_monitor_order_status_position_when_no_orders(self):
        adapter = _MockHyperliquidAdapter()
        adapter.get_open_orders = lambda addr: []
        executor = LiveExecutor(hyperliquid_adapter=adapter, address="0xABC")
        results = executor.monitor_open_trades()
        assert results[0].order_status == "POSITION"
        assert results[0].exchange_order_id == ""

    def test_live_monitor_result_dataclass(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        r = LiveMonitorResult(
            symbol="BTCUSDT",
            side="LONG",
            size=1.0,
            entry_price=50000.0,
            mark_price=50500.0,
            unrealized_pnl=500.0,
            liquidation_price=45000.0,
            order_status="open",
            exchange_order_id="oid-1",
            timestamp=now,
        )
        assert r.symbol == "BTCUSDT"
        assert r.side == "LONG"
        assert r.size == 1.0
        assert r.entry_price == 50000.0
        assert r.mark_price == 50500.0
        assert r.unrealized_pnl == 500.0
        assert r.liquidation_price == 45000.0
        assert r.order_status == "open"
        assert r.exchange_order_id == "oid-1"

    def test_monitor_zero_size_position_skipped(self):
        adapter = _MockHyperliquidAdapter()
        adapter.get_positions = lambda addr: [
            Position(coin="BTC", size=0.0, entry_px=50000.0, unrealized_pnl=0.0, liquidation_px=0.0),
        ]
        executor = LiveExecutor(hyperliquid_adapter=adapter, address="0xABC")
        results = executor.monitor_open_trades()
        assert results == []


class TestExecutionRouter:

    def test_default_mode_is_paper(self):
        router = ExecutionRouter()
        assert router.mode == TradingMode.PAPER

    def test_live_mode_routes_to_live_executor(self):
        adapter = _MockExchangeAdapter()
        live_executor = LiveExecutor(exchange_adapter=adapter)
        router = ExecutionRouter(live_executor=live_executor, mode=TradingMode.LIVE)
        result = router.execute(_MockCandidate(), _SIZE_1)
        assert hasattr(result, "accepted")
        assert result.accepted is True
        assert result.mode == "LIVE"

    def test_paper_mode_executes_via_paper_executor(self):
        mock_paper = _MockPaperExecutor()
        router = ExecutionRouter(
            paper_executor=mock_paper,
            mode=TradingMode.PAPER,
        )
        result = router.execute(_MockCandidate(), _SIZE_1)
        assert result is not None
        assert result.id == 42
        assert len(mock_paper.calls) == 1
        call = mock_paper.calls[0]
        assert call["symbol"] == "BTCUSDT"
        assert call["side"] == "LONG"

    def test_live_mode_returns_live_order_result(self):
        adapter = _MockExchangeAdapter()
        live_executor = LiveExecutor(exchange_adapter=adapter)
        router = ExecutionRouter(live_executor=live_executor, mode=TradingMode.LIVE)
        result = router.execute(_MockCandidate(), _SIZE_1)
        assert hasattr(result, "accepted")
        assert result.accepted is True
        assert result.mode == "LIVE"

    def test_live_mode_monitor_returns_empty_list(self):
        live_executor = LiveExecutor()
        router = ExecutionRouter(live_executor=live_executor, mode=TradingMode.LIVE)
        results = router.monitor_open_trades()
        assert results == []

    def test_live_mode_without_executor_raises(self):
        router = ExecutionRouter(mode=TradingMode.LIVE)
        import pytest
        with pytest.raises(RuntimeError, match="LiveExecutor not configured"):
            router.execute(_MockCandidate(), _SIZE_1)

    def test_live_mode_monitor_without_executor_raises(self):
        router = ExecutionRouter(mode=TradingMode.LIVE)
        import pytest
        with pytest.raises(RuntimeError, match="LiveExecutor not configured"):
            router.monitor_open_trades()

    def test_paper_mode_monitor_uses_paper_executor(self):
        mock_paper = _MockPaperExecutor()
        router = ExecutionRouter(
            paper_executor=mock_paper,
            mode=TradingMode.PAPER,
        )
        results = router.monitor_open_trades()
        assert results == []

    def test_trading_mode_enum_values(self):
        assert TradingMode.PAPER.value == "PAPER"
        assert TradingMode.LIVE.value == "LIVE"
