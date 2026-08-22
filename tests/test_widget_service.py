from __future__ import annotations

from datetime import UTC, datetime, timedelta

from database import PaperTrade, Trade
from services.widget_service import WidgetService


def test_portfolio_widget_mixed_quantity_btc_eth(db_session):
    """BTC LONG entry 60000 -> exit 61000, quantity 0.05: real $ P&L = $50.
    ETH SHORT entry 3000 -> exit 2950, quantity 2: real $ P&L = $100.
    Raw sum of Trade.pnl = 1000 + 50 = 1050 (wrong). Real combined total = $150.
    """
    now = datetime.now(UTC)

    btc_trade = Trade(
        id=20,
        symbol="BTCUSDT",
        side="LONG",
        entry=60000.0,
        pnl=1000.0,
        status="CLOSED",
        created_at=now - timedelta(hours=2),
        closed_at=now - timedelta(hours=1),
    )
    db_session.add(btc_trade)
    db_session.add(PaperTrade(
        id=20,
        position_id=20,
        symbol="BTCUSDT",
        side="LONG",
        entry=60000.0,
        exit_price=61000.0,
        quantity=0.05,
        pnl=1000.0,
        status="CLOSED",
    ))

    eth_trade = Trade(
        id=21,
        symbol="ETHUSDT",
        side="SHORT",
        entry=3000.0,
        pnl=50.0,
        status="CLOSED",
        created_at=now - timedelta(hours=4),
        closed_at=now - timedelta(hours=3),
    )
    db_session.add(eth_trade)
    db_session.add(PaperTrade(
        id=21,
        position_id=21,
        symbol="ETHUSDT",
        side="SHORT",
        entry=3000.0,
        exit_price=2950.0,
        quantity=2.0,
        pnl=50.0,
        status="CLOSED",
    ))

    db_session.flush()

    svc = WidgetService(session_factory=lambda: db_session)
    widget = svc._portfolio_widget()

    assert widget["total_pnl"] == 150.0
    assert widget["total_trades"] == 2
    assert widget["win_rate"] == 100.0


def test_portfolio_widget_no_matching_paper_trade_is_excluded(db_session):
    # Real quantity is unknown without a matching PaperTrade -- must be
    # excluded entirely, not treated as if quantity=1.0. Corrected
    # 2026-08-22: mirrors risk_manager.py's/paper_executor.py's
    # established "exclude, don't guess" handling of the identical
    # condition -- an earlier version of this test asserted the opposite
    # (a quantity=1.0 guess), which was itself the bug.
    trade = Trade(
        id=22,
        symbol="SOLUSDT",
        side="LONG",
        entry=150.0,
        pnl=5.0,
        status="CLOSED",
        created_at=datetime.now(UTC),
        closed_at=datetime.now(UTC),
    )
    db_session.add(trade)
    db_session.flush()

    svc = WidgetService(session_factory=lambda: db_session)
    widget = svc._portfolio_widget()

    assert widget["total_pnl"] == 0.0
    assert widget["total_trades"] == 0
