from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional

from config import (
    ACCOUNT_EQUITY,
    MAX_EXPOSURE_PER_SYMBOL,
    MAX_OPEN_TRADES,
    MAX_PORTFOLIO_EXPOSURE,
)
from core.health_check import HealthCheck
from core.kill_switch import KillSwitch
from dashboard.metrics import MetricsCollector
from dashboard.schemas import (
    ActivityItem,
    ActivityResponse,
    OverviewResponse,
    PortfolioSummaryResponse,
    RiskSummaryResponse,
    StatsResponse,
)
from performance_engine import PerformanceEngine
from portfolio_engine import PortfolioEngine


class DashboardService:
    def __init__(
        self,
        kill_switch: KillSwitch,
        health_check: HealthCheck,
        portfolio_engine: PortfolioEngine,
        performance_engine: PerformanceEngine,
        metrics: MetricsCollector,
        session_factory: Callable[[], Any],
        trading_mode: str = "PAPER",
        dry_run: bool = True,
    ) -> None:
        self._kill_switch = kill_switch
        self._health_check = health_check
        self._portfolio_engine = portfolio_engine
        self._performance_engine = performance_engine
        self._metrics = metrics
        self._session_factory = session_factory
        self._trading_mode = trading_mode
        self._dry_run = dry_run

    def overview(self) -> OverviewResponse:
        ks = self._kill_switch
        portfolio = self._portfolio_engine.stats()

        return OverviewResponse(
            engine_status=ks.state().value,
            mode=self._trading_mode,
            equity=round(ACCOUNT_EQUITY + portfolio.total_pnl, 2),
            open_trades=portfolio.open_trades,
            risk_level=self._compute_risk_level(portfolio),
        )

    def stats(self) -> StatsResponse:
        perf = self._performance_engine.stats()
        portfolio = self._portfolio_engine.stats()
        avg_return = (
            round(portfolio.total_pnl / portfolio.total_trades, 2)
            if portfolio.total_trades > 0
            else 0.0
        )
        return StatsResponse(
            total_trades=portfolio.total_trades,
            win_rate=portfolio.win_rate,
            pnl=portfolio.total_pnl,
            average_return=avg_return,
        )

    def portfolio(self) -> PortfolioSummaryResponse:
        portfolio = self._portfolio_engine.stats()
        equity = round(ACCOUNT_EQUITY + portfolio.total_pnl, 2)
        exposure = portfolio.current_open_exposure
        return PortfolioSummaryResponse(
            equity=equity,
            exposure=exposure,
            open_positions=portfolio.open_trades,
            available_balance=round(equity - exposure, 2),
        )

    def risk(self) -> RiskSummaryResponse:
        portfolio = self._portfolio_engine.stats()
        session = self._session_factory()
        try:
            from database import Trade

            symbol_exposures: dict[str, float] = {}
            open_trades = session.query(Trade).filter(Trade.status == "OPEN").all()
            for t in open_trades:
                sym = str(t.symbol)
                symbol_exposures[sym] = (
                    symbol_exposures.get(sym, 0.0) + float(t.entry)
                )

            return RiskSummaryResponse(
                risk_status=self._compute_risk_status(portfolio, symbol_exposures),
                position_limits={
                    "max_open_trades": MAX_OPEN_TRADES,
                    "max_exposure_per_symbol": MAX_EXPOSURE_PER_SYMBOL,
                    "max_portfolio_exposure": MAX_PORTFOLIO_EXPOSURE,
                },
                exposure={
                    "symbols": {
                        k: {"current": round(v, 2), "limit": MAX_EXPOSURE_PER_SYMBOL}
                        for k, v in symbol_exposures.items()
                    },
                    "total": {
                        "current": round(portfolio.current_open_exposure, 2),
                        "limit": MAX_PORTFOLIO_EXPOSURE,
                    },
                    "open_trades": {
                        "current": portfolio.open_trades,
                        "limit": MAX_OPEN_TRADES,
                    },
                },
            )
        finally:
            session.close()

    def activity(self) -> ActivityResponse:
        session = self._session_factory()
        try:
            from database import Signal, Trade

            items: list[ActivityItem] = []

            recent_trades = (
                session.query(Trade)
                .order_by(Trade.created_at.desc())
                .limit(10)
                .all()
            )
            for t in recent_trades:
                ts = (
                    t.created_at.isoformat()
                    if t.created_at
                    else datetime.now(timezone.utc).isoformat()
                )
                items.append(
                    ActivityItem(
                        type="trade",
                        description=f"{t.symbol} {t.side} — {t.status}",
                        timestamp=ts,
                    )
                )

            recent_signals = (
                session.query(Signal)
                .order_by(Signal.created_at.desc())
                .limit(10)
                .all()
            )
            for s in recent_signals:
                ts = (
                    s.created_at.isoformat()
                    if s.created_at
                    else datetime.now(timezone.utc).isoformat()
                )
                items.append(
                    ActivityItem(
                        type="signal",
                        description=f"{s.symbol} {s.side} score={s.score}",
                        timestamp=ts,
                    )
                )

            items.sort(key=lambda i: i.timestamp, reverse=True)
            return ActivityResponse(activities=items[:20])
        finally:
            session.close()

    def _compute_risk_level(self, portfolio: Any) -> str:
        if portfolio.open_trades == 0:
            return "LOW"
        ratio = portfolio.open_trades / MAX_OPEN_TRADES
        exposure_ratio = (
            portfolio.current_open_exposure / MAX_PORTFOLIO_EXPOSURE
            if MAX_PORTFOLIO_EXPOSURE > 0
            else 0.0
        )
        if ratio >= 1.0 or exposure_ratio >= 0.9:
            return "HIGH"
        if ratio >= 0.5 or exposure_ratio >= 0.5:
            return "MEDIUM"
        return "LOW"

    def _compute_risk_status(self, portfolio: Any, symbol_exposures: dict[str, float]) -> str:
        if portfolio.open_trades >= MAX_OPEN_TRADES:
            return "AT_LIMIT"
        for sym, exp in symbol_exposures.items():
            if exp >= MAX_EXPOSURE_PER_SYMBOL * 0.9:
                return "CAUTION"
        if portfolio.current_open_exposure >= MAX_PORTFOLIO_EXPOSURE * 0.9:
            return "CAUTION"
        return "OK"

    def get_metrics_snapshot(self) -> dict:
        return self._metrics.snapshot()
