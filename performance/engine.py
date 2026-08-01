from __future__ import annotations

import math
import logging
from datetime import datetime, timezone, timedelta
from statistics import mean, stdev
from typing import Any, Callable, Optional

from database import (
    CLOSED,
    OPEN,
    STOP_LOSS,
    TAKE_PROFIT,
    TP_HIT,
    SL_HIT,
    CANCEL,
    PaperTrade as PaperTradeModel,
    Trade,
    get_session,
)
from portfolio.core import PortfolioSnapshot
from performance.core import PerformanceReport

logger = logging.getLogger(__name__)

_RFR = 0.0
_INFINITE = 999.99
_PAPER_TERMINAL = frozenset({TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL})


class PerformanceEngine:

    def __init__(
        self,
        session_factory: Optional[Callable[[], Any]] = None,
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
        all_paper = session.query(PaperTradeModel).all()
        closed_paper = [pt for pt in all_paper if pt.status in _PAPER_TERMINAL]

        if not closed_paper:
            return PerformanceReport()

        # Build (pnl_total, trade_obj) pairs sorted by close time
        trade_pnls: list[tuple[float, PaperTradeModel]] = []
        for pt in closed_paper:
            pnl_total = float(pt.pnl or 0) * float(pt.quantity or 0)
            trade_pnls.append((pnl_total, pt))

        all_trades = session.query(Trade).all()
        trade_by_id = {t.id: t for t in all_trades}

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
            key=lambda x: _get_close_time(x[1], trade_by_id),
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
        for pt in closed_paper:
            trade = trade_by_id.get(pt.position_id)
            if trade is not None and trade.created_at is not None and trade.closed_at is not None:
                delta = trade.closed_at - trade.created_at
                holding_times.append(delta.total_seconds() / 3600)
        avg_hold = mean(holding_times) if holding_times else 0.0

        # --- 14  Trade Frequency (trades per day) ---
        if holding_times and len(closed_paper) > 0:
            oldest: Optional[datetime] = None
            newest: Optional[datetime] = None
            for pt in closed_paper:
                trade = trade_by_id.get(pt.position_id)
                if trade is not None:
                    if trade.created_at is not None and (oldest is None or trade.created_at < oldest):
                        oldest = trade.created_at
                    if trade.closed_at is not None and (newest is None or trade.closed_at > newest):
                        newest = trade.closed_at
            if oldest is not None and newest is not None:
                days_span = max((newest - oldest).total_seconds() / 86400, 1.0)
            else:
                days_span = 1.0
            freq = len(closed_paper) / days_span
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


def _get_close_time(
    pt: PaperTradeModel,
    trade_by_id: dict[int, Any],
) -> datetime:
    trade = trade_by_id.get(pt.position_id)
    if trade is not None and trade.closed_at is not None:
        return trade.closed_at
    return datetime.min
