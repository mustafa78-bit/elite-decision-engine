"""Tests for the root-level portfolio_engine.py's PortfolioEngine.

Not to be confused with the `portfolio` package's own PortfolioEngine
(tests/test_portfolio_engine.py covers that one, via `from portfolio import
PortfolioEngine` -- Python resolves that to portfolio/__init__.py, a
genuinely different class). This module is the one actually wired to
GET /portfolio (api/routes/portfolio.py) and services/terminal_service.py --
real, user-facing, and had zero test coverage before this file.
"""

import pytest

from database import PaperTrade, Trade
from portfolio_engine import PortfolioEngine


def _make_trade(db_session, **overrides):
    kwargs = dict(
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49250.0,
        tp1=51000.0,
        status="OPEN",
        pnl=None,
    )
    kwargs.update(overrides)
    t = Trade(**kwargs)
    db_session.add(t)
    db_session.flush()
    return t


def _make_paper_trade(db_session, **overrides):
    kwargs = dict(
        order_id=1,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        quantity=1.0,
        pnl=0.0,
        status="OPEN",
    )
    kwargs.update(overrides)
    pt = PaperTrade(**kwargs)
    db_session.add(pt)
    db_session.flush()
    return pt


def test_empty_portfolio(session_factory):
    engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000.0)
    stats = engine.stats()
    assert stats.current_open_exposure == 0.0
    assert stats.allocation == {}
    assert stats.equity == 10000.0


def test_exposure_and_allocation_use_real_quantity_not_raw_entry_price(session_factory, db_session):
    # Regression: current_open_exposure/allocation used to sum raw t.entry
    # (a per-unit price) directly, as if it were the position's dollar
    # value. Confirmed live 2026-08-21: a real TRXUSDT position (entry
    # $0.3392, quantity ~72916.86) displayed as ~$0 exposure instead of its
    # real ~$24,742 notional -- cheap-per-unit symbols always rounded to $0
    # regardless of real position size, while a coincidentally
    # dollar-scale-priced symbol (entry ~$228) looked plausible only by
    # accident.
    trade = _make_trade(db_session, symbol="TRXUSDT", entry=0.3392)
    _make_paper_trade(db_session, position_id=trade.id, symbol="TRXUSDT", entry=0.3392, quantity=72916.8551245)

    engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000.0)
    stats = engine.stats()

    expected = 0.3392 * 72916.8551245
    assert stats.current_open_exposure == round(expected, 2)
    assert stats.allocation["TRXUSDT"] == pytest.approx(expected)


def test_allocation_sums_multiple_symbols_by_real_notional(session_factory, db_session):
    t1 = _make_trade(db_session, symbol="BTCUSDT", entry=50000.0)
    _make_paper_trade(db_session, position_id=t1.id, symbol="BTCUSDT", entry=50000.0, quantity=0.1)
    t2 = _make_trade(db_session, symbol="ETHUSDT", entry=2000.0)
    _make_paper_trade(db_session, position_id=t2.id, symbol="ETHUSDT", entry=2000.0, quantity=2.0)

    engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000.0)
    stats = engine.stats()

    assert stats.allocation["BTCUSDT"] == 5000.0  # 50000 * 0.1
    assert stats.allocation["ETHUSDT"] == 4000.0  # 2000 * 2.0
    assert stats.current_open_exposure == 9000.0


def test_closed_trade_with_no_pnl_data_is_excluded_from_pnl_but_still_counted(session_factory, db_session):
    # Regression for the services/pnl.py migration: trade_dollar_pnl()
    # coerces a None Trade.pnl to 0.0, but this engine's own get_real_pnl()
    # wrapper must keep excluding it entirely (not silently treat "no data
    # yet" as "a real, decided zero") -- otherwise a trade with unknown PnL
    # would start counting as break-even in win/loss classification and
    # total_pnl's sum instead of being left out, while still correctly
    # contributing to closed_trades' raw count.
    winner = _make_trade(db_session, symbol="BTCUSDT", status="CLOSED", pnl=10.0)
    _make_paper_trade(db_session, position_id=winner.id, symbol="BTCUSDT", quantity=2.0, status="CLOSED")
    _make_trade(db_session, symbol="ETHUSDT", status="CLOSED", pnl=None)

    engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000.0)
    stats = engine.stats()

    assert stats.closed_trades == 2
    assert stats.winning_trades == 1
    assert stats.losing_trades == 0
    assert stats.total_pnl == 20.0  # only the winner's 10.0 * quantity 2.0, the None-pnl trade excluded


def test_excludes_exposure_when_no_paper_trade_match(session_factory, db_session):
    # No matching PaperTrade row exists for this Trade -- real quantity is
    # unknown, so this must be excluded from exposure/allocation entirely
    # (contributes 0, not a guessed quantity=1.0 * entry). Corrected
    # 2026-08-22: mirrors risk_manager.py's/paper_executor.py's established
    # "exclude, don't guess" handling of the identical missing-PaperTrade
    # condition -- an earlier version of this test asserted the opposite
    # (a quantity=1.0 guess), which was itself the bug.
    _make_trade(db_session, symbol="SOLUSDT", entry=100.0)

    engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000.0)
    stats = engine.stats()

    assert stats.current_open_exposure == 0.0
    assert stats.allocation["SOLUSDT"] == 0.0
