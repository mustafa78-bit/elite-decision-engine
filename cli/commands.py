"""CLI commands for the Elite Decision Engine.

Each command is a callable that takes **kwargs for dependency injection
and returns a string suitable for stdout.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

import config
from cli.formatter import heading, kv, status_line, table
from core.health_check import HealthCheck, HealthReport, HealthStatus
from core.kill_switch import KillSwitch
from database import Trade, get_session
from execution.router import TradingMode
from performance_engine import PerformanceEngine
from portfolio_engine import PortfolioEngine

logger = logging.getLogger(__name__)


def cmd_status(
    kill_switch: Optional[KillSwitch] = None,
    **kwargs: Any,
) -> str:
    ks = kill_switch or KillSwitch()
    dry_run = getattr(config, "DRY_RUN", True)
    mode = "PAPER"
    lines: list[str] = []
    lines.append(heading("Engine Status"))
    lines.append(kv("Engine", "Elite Decision Engine"))
    lines.append(kv("KillSwitch", ks.state().value))
    lines.append(kv("Running", ks.is_running()))
    lines.append(kv("Dry Run", dry_run))
    lines.append(kv("Trading Mode", mode))
    return "\n".join(lines)


def cmd_health(
    health_check: Optional[HealthCheck] = None,
    **kwargs: Any,
) -> str:
    hc = health_check or HealthCheck()
    report = hc.run()
    lines: list[str] = []
    lines.append(heading("Health Check"))
    lines.append(kv("Overall", report.overall_status.value))
    lines.append(kv("Duration (ms)", report.duration_ms))
    for name, status in report.checks.items():
        lines.append(kv(name, status.value, indent=1))
    for w in report.warnings:
        lines.append(status_line(f"⚠  {w}"))
    for e in report.errors:
        lines.append(status_line(f"✖  {e}"))
    return "\n".join(lines)


def cmd_portfolio(
    portfolio_engine: Optional[PortfolioEngine] = None,
    **kwargs: Any,
) -> str:
    pe = portfolio_engine or PortfolioEngine()
    stats = pe.stats()
    lines: list[str] = []
    lines.append(heading("Portfolio"))
    lines.append(kv("Total Trades", stats.total_trades))
    lines.append(kv("Open Trades", stats.open_trades))
    lines.append(kv("Closed Trades", stats.closed_trades))
    lines.append(kv("Winning Trades", stats.winning_trades))
    lines.append(kv("Losing Trades", stats.losing_trades))
    lines.append(kv("Win Rate", f"{stats.win_rate}%"))
    lines.append(kv("Total PnL", f"${stats.total_pnl:.2f}"))
    lines.append(kv("Daily PnL", f"${stats.daily_pnl:.2f}"))
    lines.append(kv("Average Win", f"${stats.average_win:.2f}"))
    lines.append(kv("Average Loss", f"${stats.average_loss:.2f}"))
    lines.append(kv("Profit Factor", stats.profit_factor))
    lines.append(kv("Max Drawdown", f"{stats.max_drawdown}%"))
    lines.append(kv("Open Exposure", f"${stats.current_open_exposure:.2f}"))
    return "\n".join(lines)


def cmd_trades(
    session_factory: Optional[Callable[[], Any]] = None,
    **kwargs: Any,
) -> str:
    sf = session_factory or get_session
    session = sf()
    try:
        open_trades = (
            session.query(Trade).filter(Trade.status == "OPEN").all()
        )
        closed_trades = (
            session.query(Trade)
            .filter(Trade.status.in_(["TP_HIT", "SL_HIT", "CLOSED"]))
            .all()
        )
    finally:
        session.close()

    lines: list[str] = []

    lines.append(heading("Open Trades"))
    if open_trades:
        header = ["ID", "Symbol", "Side", "Entry", "PnL"]
        rows = [
            [str(t.id), str(t.symbol), str(t.side), str(t.entry), str(t.pnl)]
            for t in open_trades
        ]
        lines.append(table(rows, header))
    else:
        lines.append(status_line("No open trades"))

    lines.append("")
    lines.append(heading("Closed Trades"))
    if closed_trades:
        header = ["ID", "Symbol", "Side", "PnL", "Reason"]
        rows = [
            [
                str(t.id),
                str(t.symbol),
                str(t.side),
                str(t.pnl),
                str(t.close_reason or "?"),
            ]
            for t in closed_trades
        ]
        lines.append(table(rows, header))
    else:
        lines.append(status_line("No closed trades"))

    return "\n".join(lines)


def cmd_performance(
    performance_engine: Optional[PerformanceEngine] = None,
    **kwargs: Any,
) -> str:
    pe = performance_engine or PerformanceEngine()
    stats = pe.stats()
    lines: list[str] = []
    lines.append(heading("Performance"))
    lines.append(kv("Sharpe Ratio", stats.sharpe_ratio))
    lines.append(kv("Sortino Ratio", stats.sortino_ratio))
    lines.append(kv("Profit Factor", stats.profit_factor))
    lines.append(kv("Expectancy", stats.expectancy))
    lines.append(kv("Recovery Factor", stats.recovery_factor))
    lines.append(kv("Calmar Ratio", stats.calmar_ratio))
    lines.append(kv("Avg R Multiple", stats.average_r_multiple))
    lines.append(kv("Avg Holding (hrs)", stats.average_holding_hours))
    lines.append(kv("Consecutive Wins", stats.consecutive_wins))
    lines.append(kv("Consecutive Losses", stats.consecutive_losses))
    lines.append(kv("Best Trade", f"${stats.best_trade:.2f}"))
    lines.append(kv("Worst Trade", f"${stats.worst_trade:.2f}"))
    return "\n".join(lines)


COMMANDS: dict[str, Any] = {
    "status": cmd_status,
    "health": cmd_health,
    "portfolio": cmd_portfolio,
    "trades": cmd_trades,
    "performance": cmd_performance,
}
