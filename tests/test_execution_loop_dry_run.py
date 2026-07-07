"""Deterministic tests for ExecutionLoop dry-run mode.

LIVE + DRY_RUN must call prepare_order(), NOT execute(),
and return submitted=False.

PAPER mode is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock
from typing import Any, Optional

from config import DRY_RUN
from execution.execution_loop import ExecutionLoop
from execution.live_executor import LiveExecutor, LiveOrderResult
from execution.router import ExecutionRouter, TradingMode


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
    """Always returns an approved candidate."""

    def evaluate(self, signal):
        return _MockCandidate(
            signal=_MockSignal(id=getattr(signal, "id", 1)),
        )


class _MockPipelineNone:
    """Always returns None — signal rejected."""

    def evaluate(self, signal):
        return None


class _MockSize:
    quantity: float = 1.0
    notional_value: float = 50000.0
    risk_amount: float = 750.0


class _MockRiskManager:
    def can_open_trade(self, candidate):
        return True, ""


class _MockRiskManagerBlock:
    def can_open_trade(self, candidate):
        return False, "blocked by risk manager"


class _MockPositionSizer:
    def calculate(self, candidate):
        return _MockSize()


class _MockLiveExecutorRecording:
    """Records which methods are called."""

    def __init__(self):
        self.prepare_order_calls = []
        self.execute_calls = []

    def prepare_order(self, candidate, size):
        self.prepare_order_calls.append((candidate, size))
        return {
            "ready": True,
            "validated": True,
            "signed": True,
            "submitted": False,
        }

    def execute(self, candidate, size):
        self.execute_calls.append((candidate, size))
        return LiveOrderResult(accepted=True, client_order_id="executed-oid")

    def monitor_open_trades(self):
        return []


def test_config_dry_run_default_is_true():
    assert DRY_RUN is True


class TestExecutionLoopDryRun:

    def test_live_dry_run_calls_prepare_order_not_execute(self):
        recorder = _MockLiveExecutorRecording()
        router = ExecutionRouter(
            live_executor=recorder,
            mode=TradingMode.LIVE,
        )
        loop = ExecutionLoop(
            pipeline=_MockPipeline(),
            paper_executor=MagicMock(),
            risk_manager=_MockRiskManager(),
            position_sizer=_MockPositionSizer(),
            execution_router=router,
            dry_run=True,
        )
        signal = _MockSignal()
        result = loop.process_signal(signal)

        assert result is None
        assert len(recorder.prepare_order_calls) == 1
        assert len(recorder.execute_calls) == 0

    def test_live_dry_run_does_not_create_trade(self):
        recorder = _MockLiveExecutorRecording()
        router = ExecutionRouter(
            live_executor=recorder,
            mode=TradingMode.LIVE,
        )
        loop = ExecutionLoop(
            pipeline=_MockPipeline(),
            paper_executor=MagicMock(),
            risk_manager=_MockRiskManager(),
            position_sizer=_MockPositionSizer(),
            execution_router=router,
            dry_run=True,
        )
        result = loop.process_signal(_MockSignal())
        assert result is None

    def test_paper_mode_unchanged(self):
        recorder = _MockLiveExecutorRecording()
        router = ExecutionRouter(
            live_executor=recorder,
            mode=TradingMode.PAPER,
        )
        loop = ExecutionLoop(
            pipeline=_MockPipeline(),
            paper_executor=MagicMock(),
            risk_manager=_MockRiskManager(),
            position_sizer=_MockPositionSizer(),
            execution_router=router,
            dry_run=True,
        )
        result = loop.process_signal(_MockSignal())
        assert len(recorder.execute_calls) == 0
        assert len(recorder.prepare_order_calls) == 0

    def test_live_dry_run_with_risk_block_stops_before_prepare(self):
        recorder = _MockLiveExecutorRecording()
        router = ExecutionRouter(
            live_executor=recorder,
            mode=TradingMode.LIVE,
        )
        loop = ExecutionLoop(
            pipeline=_MockPipeline(),
            paper_executor=MagicMock(),
            risk_manager=_MockRiskManagerBlock(),
            position_sizer=_MockPositionSizer(),
            execution_router=router,
            dry_run=True,
        )
        result = loop.process_signal(_MockSignal())
        assert result is None
        assert len(recorder.prepare_order_calls) == 0

    def test_live_dry_run_rejected_pipeline_stops_early(self):
        recorder = _MockLiveExecutorRecording()
        router = ExecutionRouter(
            live_executor=recorder,
            mode=TradingMode.LIVE,
        )
        loop = ExecutionLoop(
            pipeline=_MockPipelineNone(),
            paper_executor=MagicMock(),
            risk_manager=_MockRiskManager(),
            position_sizer=_MockPositionSizer(),
            execution_router=router,
            dry_run=True,
        )
        result = loop.process_signal(_MockSignal())
        assert result is None
        assert len(recorder.prepare_order_calls) == 0


class TestExecutionRouterPrepareOrder:

    def test_prepare_order_live_mode_returns_result(self):
        executor = LiveExecutor()
        router = ExecutionRouter(
            live_executor=executor,
            mode=TradingMode.LIVE,
        )
        result = router.prepare_order(_MockCandidate(), _MockSize())
        assert result == {
            "ready": True,
            "validated": True,
            "signed": True,
            "submitted": False,
        }

    def test_prepare_order_paper_mode_returns_error(self):
        router = ExecutionRouter(mode=TradingMode.PAPER)
        result = router.prepare_order(_MockCandidate(), _MockSize())
        assert result["ready"] is False
        assert result["validated"] is False
        assert result["submitted"] is False
        assert "errors" in result

    def test_prepare_order_live_no_executor_raises(self):
        import pytest
        router = ExecutionRouter(mode=TradingMode.LIVE)
        with pytest.raises(RuntimeError, match="LiveExecutor not configured"):
            router.prepare_order(_MockCandidate(), _MockSize())
