"""Deterministic tests for CLI commands.

No external dependencies, no HTTP, no exchange calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cli.commands import COMMANDS, cmd_health, cmd_performance, cmd_portfolio, cmd_status, cmd_trades
from cli.formatter import heading, kv, status_line, table
from core.health_check import HealthCheck, HealthReport, HealthStatus
from core.kill_switch import KillSwitch


class TestFormatter:

    def test_heading(self):
        assert heading("test") == "\n=== test ==="

    def test_kv(self):
        assert kv("key", "val") == "key: val"

    def test_kv_with_indent(self):
        assert kv("k", "v", indent=1) == "  k: v"

    def test_status_line(self):
        assert status_line("msg") == "  msg"

    def test_table_empty(self):
        assert table([], ["A", "B"]) == ""

    def test_table_single_row(self):
        result = table([["1", "2"]], ["A", "B"])
        assert "A" in result
        assert "1" in result

    def test_table_multiple_rows(self):
        rows = [["1", "abc"], ["2", "defg"]]
        result = table(rows, ["ID", "Val"])
        assert result.count("\n") >= 2


class TestCommands:

    def test_status_returns_string(self):
        result = cmd_status(kill_switch=KillSwitch())
        assert isinstance(result, str)
        assert "Engine Status" in result
        assert "RUNNING" in result
        assert "Dry Run" in result

    def test_status_shows_stopped(self):
        ks = KillSwitch()
        ks.disable()
        result = cmd_status(kill_switch=ks)
        assert "STOPPED" in result

    def test_health_returns_string(self):
        mock_hc = MagicMock(spec=HealthCheck)
        mock_hc.run.return_value = HealthReport(
            overall_status=HealthStatus.HEALTHY,
            checks={"database": HealthStatus.HEALTHY},
            duration_ms=5.0,
        )
        result = cmd_health(health_check=mock_hc)
        assert isinstance(result, str)
        assert "HEALTHY" in result

    def test_health_shows_failed(self):
        mock_hc = MagicMock(spec=HealthCheck)
        mock_hc.run.return_value = HealthReport(
            overall_status=HealthStatus.FAILED,
            checks={"database": HealthStatus.FAILED},
            errors=["DB down"],
        )
        result = cmd_health(health_check=mock_hc)
        assert "FAILED" in result
        assert "DB down" in result

    def test_portfolio_returns_string(self):
        mock_pe = MagicMock()
        mock_pe.stats.return_value = MagicMock(
            total_trades=5,
            open_trades=2,
            closed_trades=3,
            winning_trades=1,
            losing_trades=2,
            win_rate=33.33,
            total_pnl=100.0,
            daily_pnl=50.0,
            average_win=200.0,
            average_loss=-50.0,
            profit_factor=2.0,
            max_drawdown=10.0,
            current_open_exposure=5000.0,
        )
        result = cmd_portfolio(portfolio_engine=mock_pe)
        assert isinstance(result, str)
        assert "Total Trades" in result
        assert "5" in result

    def test_trades_returns_string(self):
        mock_session = MagicMock()
        mock_trade = MagicMock()
        mock_trade.id = 1
        mock_trade.symbol = "BTCUSDT"
        mock_trade.side = "LONG"
        mock_trade.entry = 50000.0
        mock_trade.pnl = 0.0
        mock_trade.status = "OPEN"
        mock_trade.close_reason = None

        mock_query = MagicMock()
        mock_query.filter.return_value.all.side_effect = [
            [mock_trade],
            [],
        ]
        mock_session.query.return_value = mock_query
        mock_session_factory = MagicMock(return_value=mock_session)

        result = cmd_trades(session_factory=mock_session_factory)
        assert isinstance(result, str)
        assert "Open Trades" in result
        assert "BTCUSDT" in result

    def test_performance_returns_string(self):
        mock_perf = MagicMock()
        mock_perf.stats.return_value = MagicMock(
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            profit_factor=2.5,
            expectancy=50.0,
            recovery_factor=3.0,
            calmar_ratio=0.5,
            average_r_multiple=1.2,
            average_holding_hours=24.0,
            consecutive_wins=3,
            consecutive_losses=2,
            best_trade=500.0,
            worst_trade=-100.0,
        )
        result = cmd_performance(performance_engine=mock_perf)
        assert isinstance(result, str)
        assert "Sharpe" in result
        assert "1.5" in result


class TestCLIModule:

    def test_cli_module_runs_status(self):
        from cli.__main__ import main
        with (
            patch("sys.argv", ["cli", "status"]),
            patch("builtins.print") as mock_print,
        ):
            main()
            output = mock_print.call_args[0][0]
            assert "Engine Status" in output

    def test_unknown_command(self):
        from cli.__main__ import main
        with (
            patch("sys.argv", ["cli", "unknown"]),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1

    def test_no_command(self):
        from cli.__main__ import main
        with (
            patch("sys.argv", ["cli"]),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        assert exc.value.code == 1

    def test_commands_dict_has_all(self):
        assert "status" in COMMANDS
        assert "health" in COMMANDS
        assert "portfolio" in COMMANDS
        assert "trades" in COMMANDS
        assert "performance" in COMMANDS
