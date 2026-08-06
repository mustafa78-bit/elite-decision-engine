from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from database import Trade, PaperTrade

def trade_dollar_pnl(trade: Trade, paper_trade: PaperTrade | None) -> float:
    """
    Computes real-dollar PnL for a trade using the corresponding PaperTrade quantity.
    Falls back to 1.0 if no PaperTrade is provided or quantity is missing.
    """
    qty = float(paper_trade.quantity) if (paper_trade is not None and paper_trade.quantity is not None) else 1.0
    return (trade.pnl or 0.0) * qty

def trade_notional_exposure(trade: Trade, paper_trade: PaperTrade | None) -> float:
    """
    Computes notional exposure for a trade using the corresponding PaperTrade quantity.
    Falls back to 1.0 if no PaperTrade is provided or quantity is missing.
    """
    qty = float(paper_trade.quantity) if (paper_trade is not None and paper_trade.quantity is not None) else 1.0
    return (trade.entry or 0.0) * qty

def get_trades_with_dollar_pnl(session: Session, *filters, limit: int | None = None, **kwargs) -> list[tuple[Trade, float]]:
    """
    Queries Trade, outerjoining with PaperTrade, applying any SQLAlchemy filters,
    ordered by created_at desc (nulls last), and returns list of tuples of (Trade, dollar_pnl).
    """
    query = session.query(Trade, PaperTrade).outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
    query = query.order_by(Trade.created_at.desc().nullslast())
    for f in filters:
        query = query.filter(f)
    for k, v in kwargs.items():
        if hasattr(Trade, k):
            query = query.filter(getattr(Trade, k) == v)
    if limit is not None:
        query = query.limit(limit)
    results = query.all()
    return [(t, trade_dollar_pnl(t, pt)) for t, pt in results]

def get_trades_with_exposure(session: Session, *filters, limit: int | None = None, **kwargs) -> list[tuple[Trade, float]]:
    """
    Queries Trade, outerjoining with PaperTrade, applying any SQLAlchemy filters,
    ordered by created_at desc (nulls last), and returns list of tuples of (Trade, notional_exposure).
    """
    query = session.query(Trade, PaperTrade).outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
    query = query.order_by(Trade.created_at.desc().nullslast())
    for f in filters:
        query = query.filter(f)
    for k, v in kwargs.items():
        if hasattr(Trade, k):
            query = query.filter(getattr(Trade, k) == v)
    if limit is not None:
        query = query.limit(limit)
    results = query.all()
    return [(t, trade_notional_exposure(t, pt)) for t, pt in results]

def get_trades_with_details(session: Session, *filters, limit: int | None = None, **kwargs) -> list[tuple[Trade, PaperTrade | None, float, float]]:
    """
    Queries Trade, outerjoining with PaperTrade, applying any SQLAlchemy filters,
    ordered by created_at desc (nulls last), and returns list of tuples of (Trade, PaperTrade | None, dollar_pnl, notional_exposure).
    """
    query = session.query(Trade, PaperTrade).outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
    query = query.order_by(Trade.created_at.desc().nullslast())
    for f in filters:
        query = query.filter(f)
    for k, v in kwargs.items():
        if hasattr(Trade, k):
            query = query.filter(getattr(Trade, k) == v)
    if limit is not None:
        query = query.limit(limit)
    results = query.all()
    return [(t, pt, trade_dollar_pnl(t, pt), trade_notional_exposure(t, pt)) for t, pt in results]

# Maintain backwards compatibility with previously aliased query methods
query_trades_with_dollar_pnl = get_trades_with_dollar_pnl
query_trades_with_exposure = get_trades_with_exposure
query_trades_with_details = get_trades_with_details
