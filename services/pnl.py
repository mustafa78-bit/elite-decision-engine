"""Shared Trade.pnl (per-unit) -> real-dollar conversion helpers.

Trade.pnl is a raw per-unit price delta, not a dollar amount (see
execution/paper_executor.py's calculate_pnl()). Trade has no quantity
column -- real quantity only exists on the separate PaperTrade table,
joined via PaperTrade.position_id == Trade.id. This module is the
single place that conversion is implemented; callers should use these
helpers instead of reimplementing the join.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database import PaperTrade, Trade


def trade_dollar_pnl(trade: Trade, paper_trade: PaperTrade | None) -> float:
    """Real dollar PnL for a trade: raw per-unit pnl * real quantity.

    Falls back to the raw pnl value (quantity=1.0) when no matching
    PaperTrade exists.
    """
    qty = float(paper_trade.quantity) if (paper_trade is not None and paper_trade.quantity is not None) else 1.0
    return (trade.pnl or 0.0) * qty


def trade_notional_exposure(trade: Trade, paper_trade: PaperTrade | None) -> float:
    """Real notional exposure for a trade: entry price * real quantity.

    Falls back to the raw entry price (quantity=1.0) when no matching
    PaperTrade exists.
    """
    qty = float(paper_trade.quantity) if (paper_trade is not None and paper_trade.quantity is not None) else 1.0
    return (trade.entry or 0.0) * qty


def get_trades_with_dollar_pnl(session: Session, *filters, limit: int | None = None) -> list[tuple[Trade, float]]:
    """Query Trade outer-joined with PaperTrade, returning (Trade, dollar_pnl) pairs."""
    query = session.query(Trade, PaperTrade).outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
    for f in filters:
        query = query.filter(f)
    if limit is not None:
        query = query.limit(limit)
    results = query.all()
    return [(t, trade_dollar_pnl(t, pt)) for t, pt in results]


def get_trades_with_exposure(session: Session, *filters, limit: int | None = None) -> list[tuple[Trade, float]]:
    """Query Trade outer-joined with PaperTrade, returning (Trade, notional_exposure) pairs."""
    query = session.query(Trade, PaperTrade).outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
    for f in filters:
        query = query.filter(f)
    if limit is not None:
        query = query.limit(limit)
    results = query.all()
    return [(t, trade_notional_exposure(t, pt)) for t, pt in results]
