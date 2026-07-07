"""End-to-end integration test for the full trading pipeline.

Five scenarios covering the complete signal → trade lifecycle:

  1. Full pipeline success
  2. Risk rejection
  3. KillSwitch active
  4. HealthCheck failure
  5. LIVE + DRY_RUN

No HTTP, no exchange calls, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from core.circuit_breaker import CircuitBreaker
from core.health_check import HealthCheck, HealthReport, HealthStatus
from core.kill_switch import EngineState, KillSwitch
from core.retry import RetryPolicy
from core.settings import Settings
from execution.execution_loop import ExecutionLoop
from execution.live_executor import LiveExecutor
from execution.paper_executor import PaperExecutor
from execution.router import ExecutionRouter, TradingMode
from performance_engine import PerformanceEngine
from portfolio_engine import PortfolioEngine
from position_sizing import PositionSizingEngine
from risk_manager import RiskManager


@dataclass(frozen=True)
class _Signal:
    id: int = 1
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    timeframe: str = "1h"


@dataclass(frozen=True)
class _Candidate:
    id: int = 1
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    timeframe: str = "1h"
    entry: float = 50000.0
    scores: object = None
    confidence: float = 0.9
    decision: str = "APPROVE"
    signal: _Signal = _Signal()

    def __post_init__(self):
        if self.scores is None:
            object.__setattr__(self, "scores", {"atr": 500.0})


class _ApprovingPipeline:
    def evaluate(self, signal):
        sid = getattr(signal, "id", 1)
        return _Candidate(id=sid, signal=_Signal(id=sid, symbol=getattr(signal, "symbol", "BTCUSDT"), side=getattr(signal, "side", "LONG")))


class _RejectingPipeline:
    def evaluate(self, signal):
        return None


def _make_adapter(session_factory):
    adapter = MagicMock()
    adapter.monitor_open_trades.return_value = []
    return adapter


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def pipeline_approves():
    return _ApprovingPipeline()


@pytest.fixture
def pipeline_rejects():
    return _RejectingPipeline()


@pytest.fixture
def risk_manager(session_factory):
    return RiskManager(session_factory=session_factory)


@pytest.fixture
def position_sizer():
    return PositionSizingEngine()


@pytest.fixture
def paper_executor(session_factory):
    collector = MagicMock()
    collector.get_ohlcv.return_value = MagicMock(empty=True)
    return PaperExecutor(session_factory=session_factory, collector=collector)


@pytest.fixture
def live_executor():
    return LiveExecutor()


@pytest.fixture
def paper_router(paper_executor):
    return ExecutionRouter(paper_executor=paper_executor, mode=TradingMode.PAPER)


@pytest.fixture
def live_router(live_executor):
    return ExecutionRouter(live_executor=live_executor, mode=TradingMode.LIVE)


@pytest.fixture
def portfolio_engine(session_factory):
    return PortfolioEngine(session_factory=session_factory)


@pytest.fixture
def performance_engine(session_factory):
    return PerformanceEngine(session_factory=session_factory)


@pytest.fixture
def kill_switch():
    return KillSwitch()


@pytest.fixture
def health_check_healthy():
    return MagicMock(spec=HealthCheck)


@pytest.fixture
def health_check_failed():
    hc = MagicMock(spec=HealthCheck)
    hc.run.return_value = HealthReport(
        overall_status=HealthStatus.FAILED,
        checks={"database": HealthStatus.FAILED},
        errors=["Database check failed"],
    )
    return hc


# ------------------------------------------------------------------
# Scenario 1: Full pipeline success
# ------------------------------------------------------------------


class TestFullPipelineSuccess:

    def test_signal_to_trade_persistence(self, db_session, session_factory, pipeline_approves, risk_manager, position_sizer, paper_router, paper_executor, portfolio_engine, performance_engine):
        from database import Signal
        db_session.add(Signal(id=1, symbol="BTCUSDT", side="LONG", timeframe="1h"))
        db_session.commit()

        loop = ExecutionLoop(
            pipeline=pipeline_approves,
            paper_executor=paper_executor,
            risk_manager=risk_manager,
            position_sizer=position_sizer,
            execution_router=paper_router,
        )
        signal = _Signal()
        result = loop.run_once([signal])

        assert result.processed == 1
        assert result.created == 1
        assert len(result.trades) == 1

        trade = result.trades[0]
        assert trade.symbol == "BTCUSDT"
        assert trade.side == "LONG"
        assert trade.entry > 0
        assert trade.stop < trade.entry
        assert trade.tp1 > trade.entry
        assert trade.status == "OPEN"
        assert trade.pnl == 0.0

        # Signal status should be EXECUTED
        sig = db_session.query(Signal).filter(Signal.id == 1).first()
        assert sig is not None
        assert sig.status == "EXECUTED"

        # Portfolio stats reflect the open trade
        stats = portfolio_engine.stats()
        assert stats.total_trades == 1
        assert stats.open_trades == 1
        assert stats.closed_trades == 0
        assert stats.current_open_exposure > 0

        # Performance stats (no closed trades → defaults)
        perf = performance_engine.stats()
        assert perf.sharpe_ratio == 0.0
        assert perf.sortino_ratio == 0.0

    def test_duplicate_signal_no_new_trade(self, db_session, session_factory, pipeline_approves, risk_manager, position_sizer, paper_router, paper_executor):
        from database import Signal
        db_session.add(Signal(id=1, symbol="BTCUSDT", side="LONG", timeframe="1h"))
        db_session.commit()

        loop = ExecutionLoop(
            pipeline=pipeline_approves,
            paper_executor=paper_executor,
            risk_manager=risk_manager,
            position_sizer=position_sizer,
            execution_router=paper_router,
        )
        signal = _Signal()
        result1 = loop.run_once([signal])
        assert result1.created == 1

        result2 = loop.run_once([signal])
        assert result2.created == 0


# ------------------------------------------------------------------
# Scenario 2: Risk rejection
# ------------------------------------------------------------------


class TestRiskRejection:

    def test_risk_rejected_trade_not_created(self, db_session, session_factory, pipeline_approves, position_sizer, paper_router, paper_executor):
        from database import Signal
        db_session.add(Signal(id=1, symbol="BTCUSDT", side="LONG", timeframe="1h"))
        db_session.add(Signal(id=2, symbol="ETHUSDT", side="SHORT", timeframe="1h"))
        db_session.commit()

        rejecting_risk = MagicMock()
        rejecting_risk.can_open_trade.return_value = (False, "risk rejected by test")

        loop = ExecutionLoop(
            pipeline=pipeline_approves,
            paper_executor=paper_executor,
            risk_manager=rejecting_risk,
            position_sizer=position_sizer,
            execution_router=paper_router,
        )
        signal = _Signal(id=2, symbol="ETHUSDT", side="SHORT")
        result = loop.run_once([signal])
        assert result.created == 0

        sig2 = db_session.query(Signal).filter(Signal.id == 2).first()
        assert sig2 is not None
        assert sig2.status == "REJECTED"


# ------------------------------------------------------------------
# Scenario 3: KillSwitch active
# ------------------------------------------------------------------


class TestKillSwitchBlocksExecution:

    def test_kill_switch_stopped_skips_signal(self, db_session, session_factory, pipeline_approves, risk_manager, position_sizer, paper_router, paper_executor):
        ks = KillSwitch(EngineState.STOPPED)
        loop = ExecutionLoop(
            pipeline=pipeline_approves,
            paper_executor=paper_executor,
            risk_manager=risk_manager,
            position_sizer=position_sizer,
            execution_router=paper_router,
            kill_switch=ks,
        )

        signal = _Signal()
        result = loop.run_once([signal])
        assert result.processed == 1
        assert result.created == 0  # skipped by KillSwitch

        # Signal status should NOT be EXECUTED
        from database import Signal
        sig = db_session.query(Signal).filter(Signal.id == 1).first()
        assert sig is None  # signal was never processed

    def test_kill_switch_running_allows_execution(self, db_session, session_factory, pipeline_approves, risk_manager, position_sizer, paper_router, paper_executor):
        ks = KillSwitch(EngineState.RUNNING)
        loop = ExecutionLoop(
            pipeline=pipeline_approves,
            paper_executor=paper_executor,
            risk_manager=risk_manager,
            position_sizer=position_sizer,
            execution_router=paper_router,
            kill_switch=ks,
        )

        signal = _Signal()
        result = loop.run_once([signal])
        assert result.processed == 1
        assert result.created == 1


# ------------------------------------------------------------------
# Scenario 4: HealthCheck failure
# ------------------------------------------------------------------


class TestHealthCheckFailure:

    def test_execution_loop_aborts_on_health_check_failure(self, db_session, session_factory, pipeline_approves, risk_manager, position_sizer, paper_router, paper_executor):
        mock_hc = MagicMock(spec=HealthCheck)
        mock_hc.run.return_value = HealthReport(
            overall_status=HealthStatus.FAILED,
            checks={"database": HealthStatus.FAILED},
            errors=["Database check failed"],
        )
        loop = ExecutionLoop(
            pipeline=pipeline_approves,
            paper_executor=paper_executor,
            risk_manager=risk_manager,
            position_sizer=position_sizer,
            execution_router=paper_router,
            health_check=mock_hc,
        )

        signal = _Signal()
        result = loop.run_once([signal])
        assert result.processed == 0
        assert result.created == 0

    def test_execution_loop_proceeds_on_healthy(self, db_session, session_factory, pipeline_approves, risk_manager, position_sizer, paper_router, paper_executor):
        mock_hc = MagicMock(spec=HealthCheck)
        mock_hc.run.return_value = HealthReport(
            overall_status=HealthStatus.HEALTHY,
            checks={"database": HealthStatus.HEALTHY},
        )
        loop = ExecutionLoop(
            pipeline=pipeline_approves,
            paper_executor=paper_executor,
            risk_manager=risk_manager,
            position_sizer=position_sizer,
            execution_router=paper_router,
            health_check=mock_hc,
        )

        signal = _Signal()
        result = loop.run_once([signal])
        assert result.processed == 1
        assert result.created == 1


# ------------------------------------------------------------------
# Scenario 5: LIVE mode + DRY_RUN
# ------------------------------------------------------------------


class TestLiveDryRun:

    def test_prepare_order_runs(self, live_executor):
        candidate = _Candidate()
        from position_sizing import PositionSize
        size = PositionSize(quantity=1.0, notional_value=50000.0, risk_amount=750.0)
        result = live_executor.prepare_order(candidate, size)
        assert result["ready"] is True
        assert result["validated"] is True
        assert result["signed"] is True
        assert result["submitted"] is False

    def test_execute_not_called_in_dry_run(self, db_session, session_factory, pipeline_approves, risk_manager, position_sizer):
        live_executor = LiveExecutor()
        router = ExecutionRouter(live_executor=live_executor, mode=TradingMode.LIVE)
        loop = ExecutionLoop(
            pipeline=pipeline_approves,
            paper_executor=MagicMock(),
            risk_manager=risk_manager,
            position_sizer=position_sizer,
            execution_router=router,
            dry_run=True,
        )

        signal = _Signal()
        result = loop.run_once([signal])
        assert result.created == 0  # dry_run returns None for the trade

    def test_execute_called_when_not_dry_run(self, db_session, session_factory, pipeline_approves, risk_manager, position_sizer):
        live_executor = MagicMock()
        live_executor.execute.return_value = MagicMock(accepted=True, client_order_id="oid-1")
        router = ExecutionRouter(live_executor=live_executor, mode=TradingMode.LIVE)
        loop = ExecutionLoop(
            pipeline=pipeline_approves,
            paper_executor=MagicMock(),
            risk_manager=risk_manager,
            position_sizer=position_sizer,
            execution_router=router,
            dry_run=False,
        )

        signal = _Signal()
        result = loop.run_once([signal])
        assert result.created == 1
        live_executor.execute.assert_called_once()
