from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import or_

from config import ACCOUNT_EQUITY
from database import (
    CANCEL,
    CLOSED,
    OPEN,
    SL_HIT,
    TP_HIT,
    Trade,
    get_session,
)
from database import (
    PaperTrade as PaperTradeModel,
)
from portfolio.core import PortfolioSnapshot
from services.pnl import trade_dollar_pnl

logger = logging.getLogger(__name__)

_TRADE_TERMINAL_STATUSES = frozenset({TP_HIT, SL_HIT, CLOSED, CANCEL})
_INFINITE_PF = 999.99


class PortfolioEngine:

    def __init__(
        self,
        session_factory: Callable[[], Any] | None = None,
        initial_capital: float | None = None,
    ) -> None:
        self.session_factory = session_factory or get_session
        self.initial_capital = initial_capital if initial_capital is not None else ACCOUNT_EQUITY

    def snapshot(
        self,
        current_prices: dict[str, float] | None = None,
        user_id: int | None = None,
    ) -> PortfolioSnapshot:
        session = self.session_factory()
        try:
            return self._compute(session, current_prices or {}, user_id)
        finally:
            session.close()

    def _compute(
        self,
        session: Any,
        current_prices: dict[str, float],
        user_id: int | None = None,
    ) -> PortfolioSnapshot:
        # Trade.status is the real source of truth for open/closed -- the
        # matching PaperTrade row's own .status is never actually updated by
        # the real close path (execution/paper_executor.py's
        # _close_trade_record only mutates Trade; PaperTrade.status is set
        # once at open and never transitioned in production), so filtering
        # on PaperTrade.status here would silently treat every position as
        # permanently OPEN. PaperTrade is only used below for its real
        # quantity, via the same outer join the already-fixed root
        # portfolio_engine.py uses.
        query = session.query(Trade, PaperTradeModel).outerjoin(
            PaperTradeModel, PaperTradeModel.position_id == Trade.id
        )
        if user_id is not None:
            query = query.filter(or_(Trade.user_id == user_id, Trade.user_id.is_(None)))
        results = query.all()
        open_pairs = [(t, pt) for t, pt in results if t.status == OPEN]
        closed_pairs = [(t, pt) for t, pt in results if t.status in _TRADE_TERMINAL_STATUSES]

        # ── Position count ──────────────────────────────────────────────
        position_count = len(open_pairs)

        # ── Exposure (real notional: entry price × real quantity) ──────
        # Exposure/unrealized PnL use the PaperTrade's own entry/quantity/side
        # (the real fill data), same as before this fix -- only the set of
        # *which* trades count as open changed (Trade.status-driven now).
        # A Trade with no matching PaperTrade has no real quantity to scale
        # by, so it's skipped here (same as the original PaperTrade-only
        # query implicitly did).
        exposure = 0.0
        long_exposure = 0.0
        short_exposure = 0.0
        for t, pt in open_pairs:
            if pt is None:
                continue
            val = float(pt.entry or 0) * float(pt.quantity or 0)
            exposure += val
            side = (pt.side or "").upper()
            if side == "LONG":
                long_exposure += val
            elif side == "SHORT":
                short_exposure += val

        # ── Unrealized PnL (side-aware) ─────────────────────────────────
        unrealized_pnl = 0.0
        for t, pt in open_pairs:
            if pt is None:
                continue
            price = current_prices.get(pt.symbol, float(pt.entry or 0))
            delta = price - float(pt.entry or 0)
            if (pt.side or "").upper() == "SHORT":
                delta = -delta
            unrealized_pnl += delta * float(pt.quantity or 0)

        # ── Realized PnL (per-unit pnl × real quantity) ─────────────────
        realized_pnl = 0.0
        winning_trades = 0
        losing_trades = 0
        total_wl = 0
        gross_profit = 0.0
        gross_loss = 0.0
        # Requires a real matching PaperTrade too, not just a non-null
        # Trade.pnl -- without one there's no real quantity to scale the raw
        # per-unit pnl by, and trade_dollar_pnl()'s qty=1.0 fallback would
        # inject a wrong-magnitude value into a dollar-denominated total.
        closed_with_pnl = [(t, pt) for t, pt in closed_pairs if t.pnl is not None and pt is not None]
        for t, pt in closed_with_pnl:
            pnl_val = trade_dollar_pnl(t, pt)
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
        # Cash is what's actually free -- unrealized PnL is mark-to-market
        # value tied up in open positions, not spendable cash. Only realized
        # PnL (already settled) adds to the cash balance.
        cash = self.initial_capital + realized_pnl - exposure

        win_rate = (winning_trades / total_wl * 100) if total_wl > 0 else 0.0
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = _INFINITE_PF
        else:
            profit_factor = 0.0

        # ── Equity curve & drawdown ──────────────────────────────────────
        sorted_closed = sorted(
            closed_with_pnl,
            key=lambda pair: pair[0].closed_at or pair[0].created_at,
        )
        equity_curve = [float(self.initial_capital)]
        peak = float(self.initial_capital)
        max_dd = 0.0
        for t, pt in sorted_closed:
            step = trade_dollar_pnl(t, pt)
            new_eq = equity_curve[-1] + step
            equity_curve.append(new_eq)
            if new_eq > peak:
                peak = new_eq
            if peak > 0:
                dd = (peak - new_eq) / peak
                if dd > max_dd:
                    max_dd = dd

        logger.info(
            "Portfolio metrics computed. closed_trades=%s, closed_trades_with_pnl=%s. "
            "win_rate and profit_factor are calculated over the closed_trades_with_pnl subset.",
            str(len(closed_pairs)),
            str(len(closed_with_pnl)),
        )

        return PortfolioSnapshot(
            total_equity=round(total_equity, 2),
            unrealized_pnl=round(unrealized_pnl, 2),
            realized_pnl=round(realized_pnl, 2),
            exposure=round(exposure, 2),
            long_exposure=round(long_exposure, 2),
            short_exposure=round(short_exposure, 2),
            position_count=position_count,
            cash=round(cash, 2),
            total_trades=len(results),
            open_trades=len(open_pairs),
            closed_trades=len(closed_pairs),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            total_pnl=round(total_pnl, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown=round(max_dd * 100, 2),
            equity_curve=[round(e, 2) for e in equity_curve],
            initial_capital=self.initial_capital,
            closed_trades_with_pnl=len(closed_with_pnl),
        )
