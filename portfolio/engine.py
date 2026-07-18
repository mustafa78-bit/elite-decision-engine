from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from config import ACCOUNT_EQUITY
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

logger = logging.getLogger(__name__)

_PAPER_TERMINAL_STATUSES = frozenset({TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL})
_TRADE_TERMINAL_STATUSES = frozenset({TP_HIT, SL_HIT, CLOSED, CANCEL})
_INFINITE_PF = 999.99


class PortfolioEngine:

    def __init__(
        self,
        session_factory: Optional[Callable[[], Any]] = None,
        initial_capital: Optional[float] = None,
    ) -> None:
        self.session_factory = session_factory or get_session
        self.initial_capital = initial_capital if initial_capital is not None else ACCOUNT_EQUITY

    def snapshot(
        self,
        current_prices: Optional[dict[str, float]] = None,
    ) -> PortfolioSnapshot:
        session = self.session_factory()
        try:
            return self._compute(session, current_prices or {})
        finally:
            session.close()

    def _compute(
        self,
        session: Any,
        current_prices: dict[str, float],
    ) -> PortfolioSnapshot:
        all_trades = session.query(Trade).all()
        trade_by_id = {t.id: t for t in all_trades}

        all_paper_trades = session.query(PaperTradeModel).all()
        open_paper_trades = [pt for pt in all_paper_trades if pt.status == OPEN]
        closed_paper_trades = [pt for pt in all_paper_trades if pt.status in _PAPER_TERMINAL_STATUSES]

        open_trades = [t for t in all_trades if t.status == OPEN]
        closed_trades = [t for t in all_trades if t.status in _TRADE_TERMINAL_STATUSES]

        # ── Position count ──────────────────────────────────────────────
        position_count = len(open_trades)

        # ── Exposure (from PaperTrade × quantity) ───────────────────────
        exposure = 0.0
        long_exposure = 0.0
        short_exposure = 0.0
        for pt in open_paper_trades:
            val = float(pt.entry or 0) * float(pt.quantity or 0)
            exposure += val
            if pt.side == "LONG":
                long_exposure += val
            elif pt.side == "SHORT":
                short_exposure += val

        # ── Unrealized PnL ─────────────────────────────────────────────
        unrealized_pnl = 0.0
        for pt in open_paper_trades:
            price = current_prices.get(pt.symbol, float(pt.entry or 0))
            delta = price - float(pt.entry or 0)
            if pt.side == "SHORT":
                delta = -delta
            unrealized_pnl += delta * float(pt.quantity or 0)

        # ── Realized PnL (per-unit pnl × quantity) ─────────────────────
        realized_pnl = 0.0
        winning_trades = 0
        losing_trades = 0
        total_wl = 0
        gross_profit = 0.0
        gross_loss = 0.0
        for pt in closed_paper_trades:
            pnl_val = float(pt.pnl or 0) * float(pt.quantity or 0)
            realized_pnl += pnl_val
            if pnl_val > 0:
                winning_trades += 1
                total_wl += 1
                gross_profit += pnl_val
            elif pnl_val < 0:
                losing_trades += 1
                total_wl += 1
                gross_loss += abs(pnl_val)

        total_pnl = realized_pnl + unrealized_pnl
        total_equity = self.initial_capital + total_pnl
        cash = total_equity - exposure

        win_rate = (winning_trades / total_wl * 100) if total_wl > 0 else 0.0
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = _INFINITE_PF
        else:
            profit_factor = 0.0

        # ── Equity curve & drawdown (from Trade model, PnL × rough qty) ─
        # Use PaperTrade data for equity curve when available; fall back to
        # Trade.pnl for trades without PaperTrade records.
        closed_trades_with_pnl = [
            t for t in closed_trades
            if t.pnl is not None
        ]
        sorted_closed = sorted(
            closed_trades_with_pnl,
            key=lambda t: t.closed_at or t.created_at,
        )
        equity_curve = [float(self.initial_capital)]
        peak = float(self.initial_capital)
        max_dd = 0.0
        for t in sorted_closed:
            pt = next(
                (p for p in closed_paper_trades if p.position_id == t.id),
                None,
            )
            if pt is not None:
                step = float(pt.pnl or 0) * float(pt.quantity or 0)
            else:
                step = float(t.pnl or 0)
            new_eq = equity_curve[-1] + step
            equity_curve.append(new_eq)
            if new_eq > peak:
                peak = new_eq
            if peak > 0:
                dd = (peak - new_eq) / peak
                if dd > max_dd:
                    max_dd = dd

        return PortfolioSnapshot(
            total_equity=round(total_equity, 2),
            unrealized_pnl=round(unrealized_pnl, 2),
            realized_pnl=round(realized_pnl, 2),
            exposure=round(exposure, 2),
            long_exposure=round(long_exposure, 2),
            short_exposure=round(short_exposure, 2),
            position_count=position_count,
            cash=round(cash, 2),
            total_trades=len(all_trades),
            open_trades=len(open_trades),
            closed_trades=len(closed_trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            total_pnl=round(total_pnl, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown=round(max_dd * 100, 2),
            equity_curve=[round(e, 2) for e in equity_curve],
            initial_capital=self.initial_capital,
        )
