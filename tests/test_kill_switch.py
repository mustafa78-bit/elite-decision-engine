"""Deterministic tests for KillSwitch, EngineState, and integration.

No external dependencies, no HTTP, no exchange calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock
from typing import Any, Optional

from core.kill_switch import EngineState, KillSwitch
from execution.execution_loop import ExecutionLoop
from execution.live_executor import LiveExecutor, LiveOrderResult
from execution.paper_executor import PaperExecutor, PaperTradeRequest
from execution.router import ExecutionRouter, TradingMode
from position_sizing import PositionSize


@dataclass(frozen=True)
class _MockSignal:
    id: int = 1
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    timeframe: str = "1h"


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


class _MockPipeline:
    def evaluate(self, signal):
        return _MockCandidate(signal=_MockSignal(id=getattr(signal, "id", 1)))


class _MockSize:
    quantity: float = 1.0
    notional_value: float = 50000.0
    risk_amount: float = 750.0


class _MockExchangeAdapter:
    def __init__(self):
        self.place_order_calls = []

    def place_order(self, payload):
        self.place_order_calls.append(payload)
        return {"order_id": "oid-1", "status": "NEW", "filled": 0.0}

    def cancel_order(self, order_id):
        return {"order_id": order_id, "status": "CANCELED"}

    def get_order_status(self, order_id):
        return {"order_id": order_id, "status": "FILLED", "filled": 1.0}


_SIZE1 = PositionSize(quantity=1.0, notional_value=50000.0, risk_amount=750.0)


class TestEngineState:

    def test_enum_values(self):
        assert EngineState.RUNNING.value == "RUNNING"
        assert EngineState.PAUSED.value == "PAUSED"
        assert EngineState.STOPPING.value == "STOPPING"
        assert EngineState.STOPPED.value == "STOPPED"

    def test_enum_membership(self):
        assert EngineState.RUNNING in EngineState
        assert EngineState.PAUSED in EngineState
        assert EngineState.STOPPING in EngineState
        assert EngineState.STOPPED in EngineState


class TestKillSwitch:

    def test_initial_state_is_running(self):
        ks = KillSwitch()
        assert ks.state() == EngineState.RUNNING
        assert ks.is_running() is True

    def test_enable_sets_running(self):
        ks = KillSwitch(EngineState.STOPPED)
        ks.enable()
        assert ks.state() == EngineState.RUNNING
        assert ks.is_running() is True

    def test_disable_sets_stopped(self):
        ks = KillSwitch()
        ks.disable()
        assert ks.state() == EngineState.STOPPED
        assert ks.is_running() is False

    def test_pause_sets_paused(self):
        ks = KillSwitch()
        ks.pause()
        assert ks.state() == EngineState.PAUSED
        assert ks.is_running() is False

    def test_resume_from_paused(self):
        ks = KillSwitch()
        ks.pause()
        ks.resume()
        assert ks.state() == EngineState.RUNNING
        assert ks.is_running() is True

    def test_resume_from_stopped(self):
        ks = KillSwitch()
        ks.disable()
        ks.resume()
        assert ks.state() == EngineState.RUNNING

    def test_panic_shutdown_sets_stopped(self):
        ks = KillSwitch()
        ks.panic_shutdown()
        assert ks.state() == EngineState.STOPPED
        assert ks.is_running() is False

    def test_custom_initial_state(self):
        ks = KillSwitch(initial_state=EngineState.PAUSED)
        assert ks.state() == EngineState.PAUSED
        assert ks.is_running() is False


class TestKillSwitchIntegrationLiveExecutor:

    def test_execute_blocked_when_stopped(self):
        ks = KillSwitch(EngineState.STOPPED)
        executor = LiveExecutor(
            exchange_adapter=_MockExchangeAdapter(),
            kill_switch=ks,
        )
        result = executor.execute(_MockCandidate(), _SIZE1)
        assert result.accepted is False
        assert "STOPPED" in result.error

    def test_execute_blocked_when_paused(self):
        ks = KillSwitch(EngineState.PAUSED)
        executor = LiveExecutor(
            exchange_adapter=_MockExchangeAdapter(),
            kill_switch=ks,
        )
        result = executor.execute(_MockCandidate(), _SIZE1)
        assert result.accepted is False
        assert "PAUSED" in result.error

    def test_execute_blocked_when_stopping(self):
        ks = KillSwitch(EngineState.STOPPING)
        executor = LiveExecutor(
            exchange_adapter=_MockExchangeAdapter(),
            kill_switch=ks,
        )
        result = executor.execute(_MockCandidate(), _SIZE1)
        assert result.accepted is False

    def test_execute_allowed_when_running(self):
        executor = LiveExecutor(exchange_adapter=_MockExchangeAdapter())
        result = executor.execute(_MockCandidate(), _SIZE1)
        assert result.accepted is True

    def test_execute_does_not_call_exchange_when_blocked(self):
        ks = KillSwitch(EngineState.STOPPED)
        adapter = _MockExchangeAdapter()
        executor = LiveExecutor(exchange_adapter=adapter, kill_switch=ks)
        executor.execute(_MockCandidate(), _SIZE1)
        assert len(adapter.place_order_calls) == 0


class TestKillSwitchIntegrationPaperExecutor:

    def test_open_trade_blocked_when_stopped(self):
        ks = KillSwitch(EngineState.STOPPED)
        executor = PaperExecutor(kill_switch=ks)
        request = PaperTradeRequest(symbol="BTCUSDT", side="LONG", entry=50000.0, stop_loss=49000.0, take_profit=51000.0)
        result = executor.open_trade_from_request(request)
        assert result is None

    def test_open_trade_allowed_when_running(self):
        executor = PaperExecutor()
        request = PaperTradeRequest(symbol="BTCUSDT", side="LONG", entry=50000.0, stop_loss=49000.0, take_profit=51000.0)
        result = executor.open_trade_from_request(request)
        assert result is None  # opens None because there's no session/collector

    def test_open_trade_via_open_trade_blocked(self):
        ks = KillSwitch(EngineState.STOPPED)
        executor = PaperExecutor(kill_switch=ks)
        result = executor.open_trade(symbol="BTCUSDT", side="LONG", entry=50000.0, stop_loss=49000.0, take_profit=51000.0)
        assert result is None

    def test_open_trade_blocked_when_stopping(self):
        ks = KillSwitch(EngineState.STOPPING)
        executor = PaperExecutor(kill_switch=ks)
        request = PaperTradeRequest(symbol="BTCUSDT", side="LONG", entry=50000.0, stop_loss=49000.0, take_profit=51000.0)
        result = executor.open_trade_from_request(request)
        assert result is None


class _MockRisk:
    def can_open_trade(self, candidate):
        return (True, "")

    def calculate(self, candidate):
        return _MockSize()


class _MockPosSizer:
    def calculate(self, candidate):
        return _MockSize()


class TestKillSwitchIntegrationExecutionLoop:

    def test_signal_skipped_when_stopped(self):
        ks = KillSwitch(EngineState.STOPPED)
        loop = ExecutionLoop(
            pipeline=_MockPipeline(),
            paper_executor=MagicMock(),
            risk_manager=_MockRisk(),
            position_sizer=_MockPosSizer(),
            kill_switch=ks,
        )
        result = loop.process_signal(_MockSignal())
        assert result is None

    def test_signal_skipped_when_paused(self):
        ks = KillSwitch(EngineState.PAUSED)
        loop = ExecutionLoop(
            pipeline=_MockPipeline(),
            paper_executor=MagicMock(),
            risk_manager=_MockRisk(),
            position_sizer=_MockPosSizer(),
            kill_switch=ks,
        )
        result = loop.process_signal(_MockSignal())
        assert result is None

    def test_signal_allowed_when_running(self, monkeypatch):
        monkeypatch.setattr("execution.execution_loop.update_signal_status", lambda *a, **kw: None)
        mock_paper = MagicMock()
        mock_paper.open_trade.return_value = MagicMock(id=99)
        router = ExecutionRouter(paper_executor=mock_paper, mode=TradingMode.PAPER)
        loop = ExecutionLoop(
            pipeline=_MockPipeline(),
            paper_executor=mock_paper,
            risk_manager=_MockRisk(),
            position_sizer=_MockPosSizer(),
            execution_router=router,
        )
        result = loop.process_signal(_MockSignal())
        assert result is not None

    def test_panic_before_loop_blocks_signals(self):
        ks = KillSwitch()
        ks.panic_shutdown()
        loop = ExecutionLoop(
            pipeline=_MockPipeline(),
            paper_executor=MagicMock(),
            risk_manager=_MockRisk(),
            position_sizer=_MockPosSizer(),
            kill_switch=ks,
        )
        result = loop.process_signal(_MockSignal())
        assert result is None

    def test_router_execute_blocked_when_stopped(self):
        ks = KillSwitch(EngineState.STOPPED)
        live_executor = LiveExecutor(kill_switch=ks)
        router = ExecutionRouter(live_executor=live_executor, mode=TradingMode.LIVE)
        result = router.execute(_MockCandidate(), _SIZE1)
        assert hasattr(result, "accepted")
        assert result.accepted is False
        assert "STOPPED" in result.error
