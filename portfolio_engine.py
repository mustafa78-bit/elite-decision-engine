"""Portfolio and performance tracking for the Elite Decision Engine.

Reads from the Trade database only — no side effects, no business logic
modification.  Injectable ``session_factory`` for test isolation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from config import ACCOUNT_EQUITY
from database import Trade, get_session

logger = logging.getLogger(__name__)

_CLOSED_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})
_INFINITE_PF = 999.99


@dataclass
class PortfolioStats:
    total_trades: int = 0
    open_trades: int = 0
    closed_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    loss_rate: float = 0.0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    average_pnl: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    current_open_exposure: float = 0.0
    equity_curve: list[float] = field(default_factory=list)
    equity: float = 0.0
    allocation: dict[str, float] = field(default_factory=dict)
    unrealized_pnl: float = 0.0


class PortfolioEngine:

    def __init__(
        self,
        session_factory: Optional[Callable[[], Any]] = None,
        initial_equity: Optional[float] = None,
    ) -> None:
        self.session_factory = session_factory or get_session
        self.initial_equity = initial_equity if initial_equity is not None else ACCOUNT_EQUITY

    def stats(self) -> PortfolioStats:
        session = self.session_factory()
        try:
            return self._compute(session)
        finally:
            session.close()

    def _compute(self, session: Any) -> PortfolioStats:
        all_trades = session.query(Trade).all()
        open_trades = [t for t in all_trades if t.status == "OPEN"]
        closed_trades = [t for t in all_trades if t.status in _CLOSED_STATUSES]

        open_count = len(open_trades)
        closed_count = len(closed_trades)

        winning = [t for t in closed_trades if t.pnl is not None and t.pnl > 0]
        losing = [t for t in closed_trades if t.pnl is not None and t.pnl < 0]
        win_count = len(winning)
        loss_count = len(losing)
        total_closed_wl = win_count + loss_count
        win_rate = (win_count / total_closed_wl * 100) if total_closed_wl > 0 else 0.0

        total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)

        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=None
        )
        daily_pnl = sum(
            t.pnl
            for t in closed_trades
            if t.pnl is not None
            and t.closed_at is not None
            and t.closed_at >= today_start
        )

        avg_win = sum(t.pnl for t in winning) / win_count if win_count > 0 else 0.0
        avg_loss = sum(t.pnl for t in losing) / loss_count if loss_count > 0 else 0.0

        gross_profit = sum(t.pnl for t in winning)
        gross_loss = abs(sum(t.pnl for t in losing))

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = _INFINITE_PF
        else:
            profit_factor = 0.0

        current_open_exposure = sum(t.entry for t in open_trades if t.entry is not None)

        allocation: dict[str, float] = {}
        for t in open_trades:
            sym = t.symbol or "?"
            allocation[sym] = allocation.get(sym, 0) + (t.entry or 0)

        unrealized_pnl = sum(
            (t.entry or 0) * 0.01 for t in open_trades
        )

        equity = self.initial_equity + total_pnl

        loss_count_for_rate = loss_count if (win_count + loss_count) > 0 else 1
        loss_rate = (loss_count / (win_count + loss_count) * 100) if (win_count + loss_count) > 0 else 0.0
        average_pnl = (total_pnl / closed_count) if closed_count > 0 else 0.0

        sorted_closed = sorted(
            [t for t in closed_trades if t.closed_at is not None and t.pnl is not None],
            key=lambda t: t.closed_at,
        )
        equity_curve = [float(self.initial_equity)]
        peak = float(self.initial_equity)
        max_dd = 0.0
        for t in sorted_closed:
            new_eq = equity_curve[-1] + t.pnl
            equity_curve.append(new_eq)
            if new_eq > peak:
                peak = new_eq
            if peak > 0:
                dd = (peak - new_eq) / peak
                if dd > max_dd:
                    max_dd = dd

        return PortfolioStats(
            total_trades=len(all_trades),
            open_trades=open_count,
            closed_trades=closed_count,
            winning_trades=win_count,
            losing_trades=loss_count,
            win_rate=round(win_rate, 2),
            loss_rate=round(loss_rate, 2),
            total_pnl=round(total_pnl, 2),
            daily_pnl=round(daily_pnl, 2),
            average_win=round(avg_win, 2),
            average_loss=round(avg_loss, 2),
            average_pnl=round(average_pnl, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown=round(max_dd * 100, 2),
            current_open_exposure=round(current_open_exposure, 2),
            equity_curve=[round(e, 2) for e in equity_curve],
            equity=round(equity, 2),
            allocation=allocation,
            unrealized_pnl=round(unrealized_pnl, 2),
        )
