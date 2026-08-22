"""Shared Trade.pnl (per-unit) -> real-dollar conversion helpers.

Trade.pnl is a raw per-unit price delta, not a dollar amount (see
execution/paper_executor.py's calculate_pnl()). Trade has no quantity
column -- real quantity only exists on the separate PaperTrade table,
joined via PaperTrade.position_id == Trade.id. This module is the
single place that conversion is implemented; callers should use these
helpers instead of reimplementing the join.

Convention: when no matching PaperTrade exists, return None rather than
guessing quantity=1.0. This mirrors risk_manager.py's and
execution/paper_executor.py's already-established "exclude, don't guess"
handling of the identical missing-PaperTrade condition -- guessing 1.0
can misstate the real dollar amount by orders of magnitude (see
tests/test_root_portfolio_engine.py's TRX regression: a cheap-per-unit
symbol's real quantity was ~72,916, nowhere near 1.0). An earlier version
of this module guessed 1.0 instead; that was a mistake, not a considered
tradeoff -- corrected 2026-08-22 once the existing convention elsewhere
in the codebase was found. Direct callers of trade_dollar_pnl()/
trade_notional_exposure() must handle None (exclude, don't sum it in
as 0 unless that's specifically the intended "no exposure" semantic).
get_trades_with_dollar_pnl()/get_trades_with_exposure() already filter
None results out, so their callers never see one.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from database import PaperTrade, Trade


def trade_dollar_pnl(trade: Trade, paper_trade: PaperTrade | None) -> float | None:
    """Real dollar PnL for a trade: raw per-unit pnl * real quantity.

    Returns None (unknown, not a guess) when no matching PaperTrade
    exists -- see module docstring.
    """
    if paper_trade is None or paper_trade.quantity is None:
        return None
    return (trade.pnl or 0.0) * float(paper_trade.quantity)


def trade_notional_exposure(trade: Trade, paper_trade: PaperTrade | None) -> float | None:
    """Real notional exposure for a trade: entry price * real quantity.

    Returns None (unknown, not a guess) when no matching PaperTrade
    exists -- see module docstring.
    """
    if paper_trade is None or paper_trade.quantity is None:
        return None
    return (trade.entry or 0.0) * float(paper_trade.quantity)


def get_trades_with_dollar_pnl(session: Session, *filters, limit: int | None = None) -> list[tuple[Trade, float]]:
    """Query Trade outer-joined with PaperTrade, returning (Trade, dollar_pnl) pairs.

    Trades with no matching PaperTrade (dollar_pnl unknown) are excluded
    from the returned list entirely -- callers always get a real float,
    never None.
    """
    query = session.query(Trade, PaperTrade).outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
    for f in filters:
        query = query.filter(f)
    if limit is not None:
        query = query.limit(limit)
    results = query.all()
    pairs = [(t, trade_dollar_pnl(t, pt)) for t, pt in results]
    return [(t, pnl) for t, pnl in pairs if pnl is not None]


def get_trades_with_exposure(session: Session, *filters, limit: int | None = None) -> list[tuple[Trade, float]]:
    """Query Trade outer-joined with PaperTrade, returning (Trade, notional_exposure) pairs.

    Trades with no matching PaperTrade (exposure unknown) are excluded
    from the returned list entirely -- callers always get a real float,
    never None.
    """
    query = session.query(Trade, PaperTrade).outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
    for f in filters:
        query = query.filter(f)
    if limit is not None:
        query = query.limit(limit)
    results = query.all()
    pairs = [(t, trade_notional_exposure(t, pt)) for t, pt in results]
    return [(t, exposure) for t, exposure in pairs if exposure is not None]


def compute_max_drawdown(chronological_pnls: list[float]) -> float:
    """Peak-to-trough dollar drawdown over a chronologically-sorted dollar PnL sequence.

    Callers own the sort order (which timestamp field defines "chronological"
    has diverged between call sites historically) -- this only does the
    peak-tracking, so migrating a call site to this helper never silently
    changes its ordering.
    """
    peak = 0.0
    max_dd = 0.0
    running = 0.0
    for pnl in chronological_pnls:
        running += pnl
        if running > peak:
            peak = running
        dd = peak - running
        if dd > max_dd:
            max_dd = dd
    return max_dd
