from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from statistics import mean, stdev
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from database import Signal, Trade, get_session

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    calmar: float = 0.0
    expectancy: float = 0.0
    avg_bars_held: float = 0.0
    win_rate_by_direction: dict[str, float] = field(default_factory=dict)
    monthly_pnl: dict[str, float] = field(default_factory=dict)


@dataclass
class WalkForwardWindow:
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_result: BacktestResult = field(default_factory=BacktestResult)
    test_result: BacktestResult = field(default_factory=BacktestResult)


@dataclass
class WalkForwardResult:
    windows: list[WalkForwardWindow] = field(default_factory=list)
    avg_train_sharpe: float = 0.0
    avg_test_sharpe: float = 0.0
    stability: float = 0.0
    combined_test_pnl: float = 0.0


class BacktestEngineV2:
    """Multi-strategy backtesting with advanced metrics and walk-forward analysis."""

    def __init__(self, session_factory: Callable[[], Any] | None = None,
                 session: Session | None = None) -> None:
        self.session_factory = session_factory or get_session
        self._session = session

    def _query_trades(self, limit: int = 1000) -> list[Trade]:
        if self._session is not None:
            return self._session.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
        session = self.session_factory()
        try:
            return session.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def _query_trades_range(self, start: datetime, end: datetime) -> list[Trade]:
        if self._session is not None:
            return (
                self._session.query(Trade)
                .filter(Trade.created_at >= start, Trade.created_at < end)
                .order_by(Trade.created_at.asc())
                .all()
            )
        session = self.session_factory()
        try:
            return (
                session.query(Trade)
                .filter(Trade.created_at >= start, Trade.created_at < end)
                .order_by(Trade.created_at.asc())
                .all()
            )
        finally:
            session.close()

    def run(self, strategy: str = "all", limit: int = 1000) -> BacktestResult:
        trades = self._query_trades(limit)
        return self._compute(trades, strategy)

    def _compute(self, trades: list[Trade], strategy: str = "all") -> BacktestResult:
        if strategy != "all":
            trades = [t for t in trades if str(t.side or "").lower() == strategy.lower()]

        closed = [t for t in trades if t.status in ("CLOSED", "TP_HIT", "SL_HIT")]
        if not closed:
            return BacktestResult()

        wins = [t for t in closed if t.pnl and t.pnl > 0]
        losses = [t for t in closed if t.pnl and t.pnl < 0]

        pnls = [t.pnl or 0 for t in closed]

        result = BacktestResult()
        result.total_trades = len(closed)
        result.wins = len(wins)
        result.losses = len(losses)
        result.win_rate = round((len(wins) / len(closed) * 100), 1) if closed else 0
        result.total_pnl = round(sum(t.pnl or 0 for t in closed), 2)
        result.avg_win = round(mean([t.pnl for t in wins]), 2) if wins else 0
        result.avg_loss = round(abs(mean([t.pnl for t in losses])), 2) if losses else 0
        result.profit_factor = round(
            sum(t.pnl or 0 for t in wins) / abs(sum(t.pnl or 0 for t in losses)), 2
        ) if losses else (len(wins) * 100)
        result.max_drawdown = round(self._max_drawdown(pnls), 2)
        result.max_drawdown_pct = round(self._max_drawdown_pct(pnls), 2)
        result.sharpe = round(self._sharpe(pnls), 4)
        result.sortino = round(self._sortino(pnls), 4)
        result.calmar = round(self._calmar(result.total_pnl, result.max_drawdown_pct), 4) if result.max_drawdown_pct > 0 else 0
        result.expectancy = round(
            (result.win_rate / 100 * result.avg_win) - ((1 - result.win_rate / 100) * result.avg_loss), 2
        ) if result.avg_win > 0 and result.avg_loss > 0 else 0

        directions: dict[str, list[float]] = {}
        for t in closed:
            side = str(t.side or "UNKNOWN")
            if side not in directions:
                directions[side] = []
            directions[side].append(1 if t.pnl and t.pnl > 0 else 0)
        result.win_rate_by_direction = {
            s: round((sum(v) / len(v)) * 100, 1) for s, v in directions.items()
        }

        monthly: dict[str, list[float]] = {}
        for t in closed:
            if t.created_at:
                key = t.created_at.strftime("%Y-%m")
                if key not in monthly:
                    monthly[key] = []
                monthly[key].append(t.pnl or 0)
        result.monthly_pnl = {k: round(sum(v), 2) for k, v in monthly.items()}

        held = [t for t in closed if t.created_at and t.closed_at]
        if held:
            result.avg_bars_held = round(
                mean([(t.closed_at - t.created_at).total_seconds() / 3600 for t in held]), 2
            )

        return result

    def walk_forward(
        self,
        window_size_days: int = 30,
        test_size_days: int = 7,
        step_days: int = 7,
        max_windows: int = 10,
    ) -> WalkForwardResult:
        trades = self._query_trades(limit=10000)
        if not trades:
            return WalkForwardResult()

        sorted_trades = sorted(trades, key=lambda t: t.created_at or datetime.min.replace(tzinfo=timezone.utc))
        if not sorted_trades[0].created_at:
            return WalkForwardResult()

        earliest = sorted_trades[0].created_at
        latest = sorted_trades[-1].created_at or datetime.now(timezone.utc)

        from datetime import timedelta
        windows: list[WalkForwardWindow] = []

        cursor = earliest
        while cursor + timedelta(days=window_size_days + test_size_days) <= latest and len(windows) < max_windows:
            train_start = cursor
            train_end = cursor + timedelta(days=window_size_days)
            test_start = train_end
            test_end = test_start + timedelta(days=test_size_days)

            train_trades = [t for t in sorted_trades if train_start <= (t.created_at or datetime.min.replace(tzinfo=timezone.utc)) < train_end]
            test_trades = [t for t in sorted_trades if test_start <= (t.created_at or datetime.min.replace(tzinfo=timezone.utc)) < test_end]

            wf = WalkForwardWindow(
                train_start=train_start.isoformat(),
                train_end=train_end.isoformat(),
                test_start=test_start.isoformat(),
                test_end=test_end.isoformat(),
                train_result=self._compute(train_trades),
                test_result=self._compute(test_trades),
            )
            windows.append(wf)
            cursor += timedelta(days=step_days)

        if not windows:
            return WalkForwardResult()

        train_sharpes = [w.train_result.sharpe for w in windows]
        test_sharpes = [w.test_result.sharpe for w in windows]
        avg_train_sharpe = round(mean(train_sharpes), 4) if train_sharpes else 0
        avg_test_sharpe = round(mean(test_sharpes), 4) if test_sharpes else 0
        stability = round(avg_test_sharpe / avg_train_sharpe, 4) if avg_train_sharpe != 0 else 0
        combined_test_pnl = round(sum(w.test_result.total_pnl for w in windows), 2)

        return WalkForwardResult(
            windows=windows,
            avg_train_sharpe=avg_train_sharpe,
            avg_test_sharpe=avg_test_sharpe,
            stability=stability,
            combined_test_pnl=combined_test_pnl,
        )

    def _max_drawdown(self, pnls: list[float]) -> float:
        if not pnls:
            return 0.0
        running_max = 0.0
        max_dd = 0.0
        cumulative = 0.0
        for p in pnls:
            cumulative += p
            if cumulative > running_max:
                running_max = cumulative
            dd = running_max - cumulative
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def _max_drawdown_pct(self, pnls: list[float], initial: float = 10000.0) -> float:
        if not pnls:
            return 0.0
        peak = initial
        max_dd = 0.0
        equity = initial
        for p in pnls:
            equity += p
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def _sharpe(self, pnls: list[float]) -> float:
        if len(pnls) < 2:
            return 0.0
        m = mean(pnls)
        s = stdev(pnls)
        return (m / s) if s > 0 else 0.0

    def _sortino(self, pnls: list[float]) -> float:
        if len(pnls) < 2:
            return 0.0
        m = mean(pnls)
        downside = [p for p in pnls if p < 0]
        if not downside:
            return (m / 1.0) if m > 0 else 0.0
        ds = stdev(downside) if len(downside) > 1 else abs(downside[0])
        return (m / ds) if ds > 0 else 0.0

    def _calmar(self, total_pnl: float, max_drawdown_pct: float) -> float:
        if max_drawdown_pct == 0:
            return 0.0
        return total_pnl / (max_drawdown_pct / 100 * 10000) if total_pnl != 0 else 0.0
