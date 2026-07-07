"""Performance analytics for the Elite Decision Engine.

Evaluates trading strategy quality — independent from PortfolioEngine.
Read-only, no side effects.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import Any, Callable, Optional

from config import ACCOUNT_EQUITY
from database import Trade, get_session

logger = logging.getLogger(__name__)

_CLOSED = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})
_RFR = 0.0  # risk-free rate default


@dataclass
class PerformanceStats:
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    recovery_factor: float = 0.0
    calmar_ratio: float = 0.0
    average_r_multiple: float = 0.0
    average_holding_hours: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    best_trade: float = 0.0
    worst_trade: float = 0.0


class PerformanceEngine:

    def __init__(
        self,
        session_factory: Callable[[], Any] = get_session,
        initial_equity: Optional[float] = None,
        risk_free_rate: float = _RFR,
    ) -> None:
        self.session_factory = session_factory
        self.initial_equity = initial_equity if initial_equity is not None else ACCOUNT_EQUITY
        self.risk_free_rate = risk_free_rate

    def stats(self) -> PerformanceStats:
        session = self.session_factory()
        try:
            return self._compute(session)
        finally:
            session.close()

    def _compute(self, session: Any) -> PerformanceStats:
        all_trades = session.query(Trade).all()
        closed = [t for t in all_trades if t.status in _CLOSED]

        if not closed:
            return PerformanceStats()

        pnls = [t.pnl for t in closed if t.pnl is not None]
        if not pnls:
            return PerformanceStats()

        # --- return series (percentage returns per trade) ---
        returns = []
        for t in closed:
            if t.pnl is not None and t.entry and t.entry > 0:
                returns.append(t.pnl / t.entry)

        mean_ret = mean(returns) if returns else 0.0
        std_ret = stdev(returns) if len(returns) >= 2 else 0.0

        # --- 1  Sharpe Ratio ---
        if std_ret > 0:
            sharpe = (mean_ret - self.risk_free_rate) / std_ret
        elif mean_ret > self.risk_free_rate:
            sharpe = 999.99
        else:
            sharpe = 0.0

        # --- 2  Sortino Ratio ---
        downside = [r for r in returns if r < 0]
        d_len = len(returns)
        downside_var = sum(r * r for r in downside) / d_len if d_len > 0 else 0.0
        downside_dev = math.sqrt(downside_var)
        if downside_dev > 0:
            sortino = (mean_ret - self.risk_free_rate) / downside_dev
        elif mean_ret > self.risk_free_rate:
            sortino = 999.99
        else:
            sortino = 0.0

        # --- 3  Profit Factor ---
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        if gross_loss > 0:
            pf = gross_profit / gross_loss
        elif gross_profit > 0:
            pf = 999.99
        else:
            pf = 0.0

        # --- 4  Expectancy ---
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        total_wl = len(wins) + len(losses)
        if total_wl > 0:
            win_rate = len(wins) / total_wl
            loss_rate = len(losses) / total_wl
            avg_win = mean(wins) if wins else 0.0
            avg_loss = mean(losses) if losses else 0.0
            expectancy = win_rate * avg_win - loss_rate * abs(avg_loss)
        else:
            expectancy = 0.0

        # --- 5  Recovery Factor ---
        total_pnl = sum(pnls)
        cum = 0.0
        peak_pnl = 0.0
        max_dd_dollars = 0.0
        for p in pnls:
            cum += p
            if cum > peak_pnl:
                peak_pnl = cum
            dd = peak_pnl - cum
            if dd > max_dd_dollars:
                max_dd_dollars = dd
        if max_dd_dollars > 0:
            recovery = total_pnl / max_dd_dollars
        elif total_pnl > 0:
            recovery = 999.99
        else:
            recovery = 0.0

        # --- 6  Calmar Ratio ---
        total_return_pct = total_pnl / self.initial_equity * 100 if self.initial_equity > 0 else 0.0
        cum_eq = float(self.initial_equity)
        peak_eq = cum_eq
        max_dd_pct = 0.0
        for p in pnls:
            cum_eq += p
            if cum_eq > peak_eq:
                peak_eq = cum_eq
            dd_pct = (peak_eq - cum_eq) / peak_eq if peak_eq > 0 else 0.0
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
        if max_dd_pct > 0:
            calmar = total_return_pct / (max_dd_pct * 100)
        elif total_pnl > 0:
            calmar = 999.99
        else:
            calmar = 0.0

        # --- 7  Average R Multiple ---
        r_multiples = []
        for t in closed:
            if t.pnl is not None and t.entry and t.stop and t.entry > 0 and t.stop > 0:
                risk = abs(t.entry - t.stop)
                if risk > 0:
                    r_multiples.append(t.pnl / risk)
        avg_r = mean(r_multiples) if r_multiples else 0.0

        # --- 8  Average Holding Time ---
        hours = []
        for t in closed:
            if t.created_at is not None and t.closed_at is not None:
                delta = t.closed_at - t.created_at
                hours.append(delta.total_seconds() / 3600)
        avg_hold = mean(hours) if hours else 0.0

        # --- 9 / 10  Consecutive Wins / Losses ---
        sorted_closed = sorted(
            [t for t in closed if t.pnl is not None],
            key=lambda t: t.closed_at or datetime.min,
        )
        cur_wins = 0
        cur_losses = 0
        max_wins = 0
        max_losses = 0
        for t in sorted_closed:
            if t.pnl > 0:
                cur_wins += 1
                cur_losses = 0
                max_wins = max(max_wins, cur_wins)
            elif t.pnl < 0:
                cur_losses += 1
                cur_wins = 0
                max_losses = max(max_losses, cur_losses)
            else:
                cur_wins = 0
                cur_losses = 0

        # --- 11 / 12  Best / Worst Trade ---
        best = max(pnls)
        worst = min(pnls)

        return PerformanceStats(
            sharpe_ratio=round(sharpe, 4),
            sortino_ratio=round(sortino, 4),
            profit_factor=round(pf, 2),
            expectancy=round(expectancy, 2),
            recovery_factor=round(recovery, 2),
            calmar_ratio=round(calmar, 4),
            average_r_multiple=round(avg_r, 2),
            average_holding_hours=round(avg_hold, 2),
            consecutive_wins=max_wins,
            consecutive_losses=max_losses,
            best_trade=round(best, 2),
            worst_trade=round(worst, 2),
        )
