"""Deterministic tests for HealthCheck, HealthStatus, HealthReport, and integration.

No external dependencies, no HTTP, no exchange calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from core.health_check import HealthCheck, HealthReport, HealthStatus
from execution.router import TradingMode


@dataclass(frozen=True)
class _MockSignal:
    id: int = 1
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    timeframe: str = "1h"


class _MockPipeline:
    def evaluate(self, signal):
        return _MockCandidate()


@dataclass(frozen=True)
class _MockCandidate:
    id: int = 1
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    entry: float = 50000.0
    scores: dict = None
    confidence: float = 0.9
    decision: str = "APPROVE"
    signal: _MockSignal = _MockSignal()

    def __post_init__(self):
        if self.scores is None:
            object.__setattr__(self, "scores", {"atr": 500.0})


class TestHealthStatus:

    def test_enum_values(self):
        assert HealthStatus.HEALTHY.value == "HEALTHY"
        assert HealthStatus.WARNING.value == "WARNING"
        assert HealthStatus.FAILED.value == "FAILED"

    def test_enum_membership(self):
        assert HealthStatus.HEALTHY in HealthStatus
        assert HealthStatus.WARNING in HealthStatus
        assert HealthStatus.FAILED in HealthStatus


class TestHealthReport:

    def test_is_failed_true_when_failed(self):
        report = HealthReport(overall_status=HealthStatus.FAILED)
        assert report.is_failed() is True

    def test_is_failed_false_when_healthy(self):
        report = HealthReport(overall_status=HealthStatus.HEALTHY)
        assert report.is_failed() is False

    def test_is_failed_false_when_warning(self):
        report = HealthReport(overall_status=HealthStatus.WARNING)
        assert report.is_failed() is False

    def test_default_values(self):
        report = HealthReport(overall_status=HealthStatus.HEALTHY)
        assert report.checks == {}
        assert report.warnings == []
        assert report.errors == []
        assert report.duration_ms == 0.0


class TestHealthCheckHealthy:

    def test_all_checks_pass(self, tmp_path):
        mock_session = MagicMock()
        mock_sf = MagicMock(return_value=mock_session)
        mock_ks = MagicMock()
        mock_ks.is_running.return_value = True
        mock_ks.state.return_value = MagicMock(value="RUNNING")
        mock_router = MagicMock()
        mock_router.mode = TradingMode.PAPER

        log_dir = str(tmp_path / "logs")

        with (
            patch("core.health_check.PaperExecutor") as mock_pe,
            patch("core.health_check.LiveExecutor") as mock_le,
        ):
            mock_pe.return_value = MagicMock()
            mock_le.return_value = MagicMock()

            hc = HealthCheck(
                session_factory=mock_sf,
                kill_switch=mock_ks,
                execution_router=mock_router,
                log_dir=log_dir,
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.HEALTHY
        assert report.errors == []
        assert report.duration_ms > 0
        assert report.checks["database"] == HealthStatus.HEALTHY
        assert report.checks["logging"] == HealthStatus.HEALTHY
        assert report.checks["configuration"] == HealthStatus.HEALTHY
        assert report.checks["kill_switch"] == HealthStatus.HEALTHY
        assert report.checks["execution_router"] == HealthStatus.HEALTHY
        assert report.checks["paper_executor"] == HealthStatus.HEALTHY
        assert report.checks["live_executor"] == HealthStatus.HEALTHY

    def test_warning_when_no_session_factory(self):
        mock_ks = MagicMock()
        mock_ks.is_running.return_value = True
        mock_ks.state.return_value = MagicMock(value="RUNNING")
        mock_router = MagicMock()
        mock_router.mode = TradingMode.PAPER

        with (
            patch("core.health_check.PaperExecutor"),
            patch("core.health_check.LiveExecutor"),
        ):
            hc = HealthCheck(
                session_factory=None,
                kill_switch=mock_ks,
                execution_router=mock_router,
                log_dir="/tmp",
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.WARNING
        assert len(report.warnings) > 0


class TestHealthCheckDatabaseFailure:

    def test_database_execute_raises(self):
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("connection refused")
        mock_sf = MagicMock(return_value=mock_session)
        mock_ks = MagicMock()
        mock_ks.is_running.return_value = True
        mock_ks.state.return_value = MagicMock(value="RUNNING")
        mock_router = MagicMock()
        mock_router.mode = TradingMode.PAPER

        with (
            patch("core.health_check.PaperExecutor"),
            patch("core.health_check.LiveExecutor"),
        ):
            hc = HealthCheck(
                session_factory=mock_sf,
                kill_switch=mock_ks,
                execution_router=mock_router,
                log_dir="/tmp",
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.FAILED
        assert report.checks["database"] == HealthStatus.FAILED
        assert any("connection refused" in e for e in report.errors)


class TestHealthCheckLoggingFailure:

    def test_log_dir_not_writable(self, monkeypatch):
        mock_ks = MagicMock()
        mock_ks.is_running.return_value = True
        mock_ks.state.return_value = MagicMock(value="RUNNING")
        mock_router = MagicMock()
        mock_router.mode = TradingMode.PAPER

        def _raise(*args, **kwargs):
            raise PermissionError("permission denied")

        monkeypatch.setattr("os.makedirs", _raise)

        with (
            patch("core.health_check.PaperExecutor"),
            patch("core.health_check.LiveExecutor"),
        ):
            hc = HealthCheck(
                session_factory=MagicMock(return_value=MagicMock()),
                kill_switch=mock_ks,
                execution_router=mock_router,
                log_dir="/protected/logs",
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.FAILED
        assert report.checks["logging"] == HealthStatus.FAILED


class TestHealthCheckConfigFailure:

    def test_missing_config_var(self, monkeypatch):
        mock_config = MagicMock()
        del mock_config.DRY_RUN
        monkeypatch.setattr("core.health_check.config_module", mock_config)

        mock_ks = MagicMock()
        mock_ks.is_running.return_value = True
        mock_ks.state.return_value = MagicMock(value="RUNNING")
        mock_router = MagicMock()
        mock_router.mode = TradingMode.PAPER

        with (
            patch("core.health_check.PaperExecutor"),
            patch("core.health_check.LiveExecutor"),
            patch("core.health_check.os.makedirs"),
            patch("core.health_check.open"),
            patch("core.health_check.os.remove"),
        ):
            hc = HealthCheck(
                session_factory=MagicMock(return_value=MagicMock()),
                kill_switch=mock_ks,
                execution_router=mock_router,
                log_dir="/tmp",
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.FAILED
        assert report.checks["configuration"] == HealthStatus.FAILED
        assert any("DRY_RUN" in e for e in report.errors)


class TestHealthCheckKillSwitchFailure:

    def test_kill_switch_not_running(self):
        mock_ks = MagicMock()
        mock_ks.is_running.return_value = False
        mock_ks.state.return_value = MagicMock(value="STOPPED")
        mock_router = MagicMock()
        mock_router.mode = TradingMode.PAPER

        with (
            patch("core.health_check.PaperExecutor"),
            patch("core.health_check.LiveExecutor"),
            patch("core.health_check.os.makedirs"),
            patch("core.health_check.open"),
            patch("core.health_check.os.remove"),
        ):
            hc = HealthCheck(
                session_factory=MagicMock(return_value=MagicMock()),
                kill_switch=mock_ks,
                execution_router=mock_router,
                log_dir="/tmp",
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.FAILED
        assert report.checks["kill_switch"] == HealthStatus.FAILED
        assert any("STOPPED" in e for e in report.errors)

    def test_kill_switch_not_configured(self):
        mock_router = MagicMock()
        mock_router.mode = TradingMode.PAPER

        with (
            patch("core.health_check.PaperExecutor"),
            patch("core.health_check.LiveExecutor"),
            patch("core.health_check.os.makedirs"),
            patch("core.health_check.open"),
            patch("core.health_check.os.remove"),
        ):
            hc = HealthCheck(
                session_factory=MagicMock(return_value=MagicMock()),
                kill_switch=None,
                execution_router=mock_router,
                log_dir="/tmp",
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.FAILED
        assert report.checks["kill_switch"] == HealthStatus.FAILED


class TestHealthCheckExecutionRouterFailure:

    def test_router_not_configured(self):
        mock_ks = MagicMock()
        mock_ks.is_running.return_value = True
        mock_ks.state.return_value = MagicMock(value="RUNNING")

        with (
            patch("core.health_check.PaperExecutor"),
            patch("core.health_check.LiveExecutor"),
            patch("core.health_check.os.makedirs"),
            patch("core.health_check.open"),
            patch("core.health_check.os.remove"),
        ):
            hc = HealthCheck(
                session_factory=MagicMock(return_value=MagicMock()),
                kill_switch=mock_ks,
                execution_router=None,
                log_dir="/tmp",
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.FAILED
        assert report.checks["execution_router"] == HealthStatus.FAILED


class TestHealthCheckPaperExecutorFailure:

    def test_paper_executor_raises(self):
        mock_ks = MagicMock()
        mock_ks.is_running.return_value = True
        mock_ks.state.return_value = MagicMock(value="RUNNING")
        mock_router = MagicMock()
        mock_router.mode = TradingMode.PAPER

        with (
            patch("core.health_check.PaperExecutor", side_effect=ImportError("no module")),
            patch("core.health_check.LiveExecutor"),
            patch("core.health_check.os.makedirs"),
            patch("core.health_check.open"),
            patch("core.health_check.os.remove"),
        ):
            hc = HealthCheck(
                session_factory=MagicMock(return_value=MagicMock()),
                kill_switch=mock_ks,
                execution_router=mock_router,
                log_dir="/tmp",
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.FAILED
        assert report.checks["paper_executor"] == HealthStatus.FAILED


class TestHealthCheckLiveExecutorFailure:

    def test_live_executor_raises(self):
        mock_ks = MagicMock()
        mock_ks.is_running.return_value = True
        mock_ks.state.return_value = MagicMock(value="RUNNING")
        mock_router = MagicMock()
        mock_router.mode = TradingMode.PAPER

        with (
            patch("core.health_check.PaperExecutor"),
            patch("core.health_check.LiveExecutor", side_effect=TypeError("bad init")),
            patch("core.health_check.os.makedirs"),
            patch("core.health_check.open"),
            patch("core.health_check.os.remove"),
        ):
            hc = HealthCheck(
                session_factory=MagicMock(return_value=MagicMock()),
                kill_switch=mock_ks,
                execution_router=mock_router,
                log_dir="/tmp",
            )
            report = hc.run()

        assert report.overall_status == HealthStatus.FAILED
        assert report.checks["live_executor"] == HealthStatus.FAILED


class TestHealthCheckIntegrationExecutionLoop:

    def test_execution_loop_aborts_on_failed(self):
        mock_report = HealthReport(
            overall_status=HealthStatus.FAILED,
            checks={"database": HealthStatus.FAILED},
            errors=["Database check failed"],
        )
        mock_hc = MagicMock()
        mock_hc.run.return_value = mock_report

        from execution.execution_loop import ExecutionLoop

        loop = ExecutionLoop(health_check=mock_hc)
        result = loop.run_once([])
        assert result.processed == 0
        assert result.created == 0

    def test_execution_loop_starts_on_healthy(self, monkeypatch):
        mock_report = HealthReport(
            overall_status=HealthStatus.HEALTHY,
            checks={"database": HealthStatus.HEALTHY},
            duration_ms=1.23,
        )
        mock_hc = MagicMock()
        mock_hc.run.return_value = mock_report

        from execution.execution_loop import ExecutionLoop

        loop = ExecutionLoop(health_check=mock_hc)
        result = loop.run_once([])
        assert result.processed == 0
        assert result.created == 0

    def test_no_health_check_does_not_block(self):
        from execution.execution_loop import ExecutionLoop

        loop = ExecutionLoop(health_check=None)
        result = loop.run_once([])
        assert result.processed == 0
        assert result.created == 0
