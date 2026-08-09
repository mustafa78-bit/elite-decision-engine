from __future__ import annotations

import logging
import math
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from statistics import mean, stdev
from typing import Any, Optional

from database import (
    CANCEL,
    CLOSED,
    SL_HIT,
    TP_HIT,
    Trade,
    get_session,
)
from database import (
    PaperTrade as PaperTradeModel,
)
from performance.core import PerformanceReport
from portfolio.core import PortfolioSnapshot
from services.pnl import trade_dollar_pnl

logger = logging.getLogger(__name__)

_RFR = 0.0
_INFINITE = 999.99
# Trade's terminal-status vocabulary (TP_HIT/SL_HIT/...), not PaperTrade's
# (TAKE_PROFIT/STOP_LOSS/...) -- Trade.status is the real source of truth,
# see the comment in _compute() below.
_TRADE_TERMINAL = frozenset({TP_HIT, SL_HIT, CLOSED, CANCEL})


class PerformanceEngine:

    def __init__(
        self,
        session_factory: Callable[[], Any] | None = None,
        risk_free_rate: float = _RFR,
    ) -> None:
        self.session_factory = session_factory or get_session
        self.risk_free_rate = risk_free_rate

    def report(
        self,
        snapshot: PortfolioSnapshot,
    ) -> PerformanceReport:
        session = self.session_factory()
        try:
            return self._compute(session, snapshot)
        finally:
            session.close()

    def _compute(
        self,
        session: Any,
        snapshot: PortfolioSnapshot,
    ) -> PerformanceReport:
        # Trade.status is the real source of truth for open/closed -- the
        # matching PaperTrade row's own .status is never actually updated by
        # the real close path in production (see portfolio/engine.py's
        # _compute() for the full explanation), so filtering on
        # PaperTrade.status here would silently always see zero closed
        # trades. PaperTrade is only used below for its real quantity.
        results = (
            session.query(Trade, PaperTradeModel)
            .outerjoin(PaperTradeModel, PaperTradeModel.position_id == Trade.id)
            .all()
        )
        closed_pairs = [
            (t, pt) for t, pt in results
            if t.status in _TRADE_TERMINAL and t.pnl is not None
        ]

        if not closed_pairs:
            return PerformanceReport()

        # Build (pnl_total, trade_obj) pairs sorted by close time
        trade_pnls: list[tuple[float, Trade]] = [
            (trade_dollar_pnl(t, pt), t) for t, pt in closed_pairs
        ]

        # ── Equity-curve based ratios ────────────────────────────────────
        equity_curve = snapshot.equity_curve
        if len(equity_curve) >= 2:
            returns = [
                (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
                for i in range(1, len(equity_curve))
                if equity_curve[i - 1] > 0
            ]
        else:
            returns = []

        # --- 1  Sharpe Ratio ---
        sharpe = 0.0
        if returns:
            mean_ret = mean(returns)
            std_ret = stdev(returns) if len(returns) >= 2 else 0.0
            n = len(returns)
            if std_ret > 0:
                sharpe = (mean_ret - self.risk_free_rate) / std_ret * math.sqrt(n)
            elif mean_ret > self.risk_free_rate:
                sharpe = _INFINITE

        # --- 2  Sortino Ratio ---
        sortino = 0.0
        if returns:
            mean_ret = mean(returns)
            n = len(returns)
            downside_var = sum(r * r for r in returns if r < 0) / n if n > 0 else 0.0
            downside_dev = math.sqrt(downside_var)
            if downside_dev > 0:
                sortino = (mean_ret - self.risk_free_rate) / downside_dev * math.sqrt(n)
            elif mean_ret > self.risk_free_rate:
                sortino = _INFINITE

        # --- 3  Calmar Ratio ---
        total_return_pct = (
            (snapshot.total_equity - snapshot.initial_capital)
            / snapshot.initial_capital
            * 100
        ) if snapshot.initial_capital > 0 else 0.0
        max_dd_pct = snapshot.max_drawdown
        if max_dd_pct > 0:
            calmar = total_return_pct / max_dd_pct
        elif total_return_pct > 0:
            calmar = _INFINITE
        else:
            calmar = 0.0

        # ── Compute from individual trade PnLs ───────────────────────────
        pnl_values = [p for p, _ in trade_pnls]
        wins = [p for p in pnl_values if p > 0]
        losses = [p for p in pnl_values if p < 0]
        n_wins = len(wins)
        n_losses = len(losses)
        total_wl = n_wins + n_losses

        avg_win = mean(wins) if wins else 0.0
        avg_loss = mean(losses) if losses else 0.0

        # --- 6  Expectancy ---
        if total_wl > 0:
            wr = n_wins / total_wl
            lr = n_losses / total_wl
            expectancy = wr * avg_win - lr * abs(avg_loss)
        else:
            expectancy = 0.0

        # --- 7  Payoff Ratio ---
        payoff = avg_win / abs(avg_loss) if avg_loss != 0 else (_INFINITE if avg_win > 0 else 0.0)

        # --- 8  Recovery Factor ---
        total_pnl = snapshot.total_pnl
        max_dd_dollars = 0.0
        peak_eq = snapshot.initial_capital
        for eq_pt in equity_curve:
            if eq_pt > peak_eq:
                peak_eq = eq_pt
            dd_dollars = peak_eq - eq_pt
            if dd_dollars > max_dd_dollars:
                max_dd_dollars = dd_dollars
        if max_dd_dollars > 0:
            recovery = total_pnl / max_dd_dollars
        elif total_pnl > 0:
            recovery = _INFINITE
        else:
            recovery = 0.0

        # --- 9 / 10  Largest Win / Largest Loss ---
        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0

        # --- 11 / 12  Consecutive Wins / Losses ---
        sorted_trades = sorted(
            trade_pnls,
            key=lambda x: _get_close_time(x[1]),
        )
        cur_wins = 0
        cur_losses = 0
        max_wins = 0
        max_losses = 0
        for pnl_val, _ in sorted_trades:
            if pnl_val > 0:
                cur_wins += 1
                cur_losses = 0
                if cur_wins > max_wins:
                    max_wins = cur_wins
            elif pnl_val < 0:
                cur_losses += 1
                cur_wins = 0
                if cur_losses > max_losses:
                    max_losses = cur_losses
            else:
                cur_wins = 0
                cur_losses = 0

        # --- 13  Average Holding Time ---
        holding_times: list[float] = []
        for _, t in trade_pnls:
            if t.created_at is not None and t.closed_at is not None:
                delta = t.closed_at - t.created_at
                holding_times.append(delta.total_seconds() / 3600)
        avg_hold = mean(holding_times) if holding_times else 0.0

        # --- 14  Trade Frequency (trades per day) ---
        if holding_times and closed_pairs:
            oldest: datetime | None = None
            newest: datetime | None = None
            for _, t in trade_pnls:
                if t.created_at is not None and (oldest is None or t.created_at < oldest):
                    oldest = t.created_at
                if t.closed_at is not None and (newest is None or t.closed_at > newest):
                    newest = t.closed_at
            if oldest is not None and newest is not None:
                days_span = max((newest - oldest).total_seconds() / 86400, 1.0)
            else:
                days_span = 1.0
            freq = len(closed_pairs) / days_span
        else:
            freq = 0.0

        return PerformanceReport(
            sharpe_ratio=round(sharpe, 4),
            sortino_ratio=round(sortino, 4),
            calmar_ratio=round(calmar, 4),
            average_win=round(avg_win, 2),
            average_loss=round(avg_loss, 2),
            expectancy=round(expectancy, 2),
            payoff_ratio=round(payoff, 2),
            recovery_factor=round(recovery, 2),
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),
            consecutive_wins=max_wins,
            consecutive_losses=max_losses,
            average_holding_time_hours=round(avg_hold, 2),
            trade_frequency_per_day=round(freq, 4),
        )


def _get_close_time(trade: Trade) -> datetime:
    if trade.closed_at is not None:
        return trade.closed_at
    # datetime.min is timezone-naive; Trade.closed_at is DateTime(timezone=True)
    # and comes back timezone-aware on a Postgres backend. Mixing naive and
    # aware datetimes in the same sort raises TypeError.
    return datetime.min.replace(tzinfo=timezone.utc)
