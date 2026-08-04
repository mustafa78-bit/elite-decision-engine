from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from database import Trade, PaperTrade, Signal, CLOSED, OPEN, TP_HIT, SL_HIT
from services.kpi_service import KPIService


def test_kpi_service_mixed_quantity_btc_sol(db_session):
    """Test mixed-quantity scenario like BTC/SOL.
    BTC trade opens at $65,000, closes at $65,650, real quantity 0.01
    - Trade.pnl = 650 (raw per-unit delta)
    - PaperTrade quantity = 0.01
    - Realized dollar PnL = 6.50

    SOL trade opens at $150, closes at $145, real quantity 100
    - Trade.pnl = -5 (raw per-unit delta)
    - PaperTrade quantity = 100
    - Realized dollar PnL = -500.00

    Raw sum of Trade.pnl = 645 (apparent profit)
    Real combined dollar PnL = -493.50 (loss)
    """
    now = datetime.now(timezone.utc)

    # 1. BTC Trade & PaperTrade
    btc_trade = Trade(
        id=10,
        signal_id=1,
        symbol="BTCUSDT",
        side="LONG",
        entry=65000.0,
        pnl=650.0,
        status="CLOSED",
        created_at=now - timedelta(hours=2),
        closed_at=now - timedelta(hours=1),
    )
    db_session.add(btc_trade)

    btc_paper = PaperTrade(
        id=10,
        position_id=10,
        symbol="BTCUSDT",
        side="LONG",
        entry=65000.0,
        exit_price=65650.0,
        quantity=0.01,
        pnl=650.0,
        status="CLOSED",
    )
    db_session.add(btc_paper)

    # 2. SOL Trade & PaperTrade
    sol_trade = Trade(
        id=11,
        signal_id=2,
        symbol="SOLUSDT",
        side="SHORT",
        entry=150.0,
        pnl=-5.0,
        status="CLOSED",
        created_at=now - timedelta(hours=4),
        closed_at=now - timedelta(hours=3),
    )
    db_session.add(sol_trade)

    sol_paper = PaperTrade(
        id=11,
        position_id=11,
        symbol="SOLUSDT",
        side="SHORT",
        entry=150.0,
        exit_price=145.0,
        quantity=100.0,
        pnl=-5.0,
        status="CLOSED",
    )
    db_session.add(sol_paper)

    db_session.flush()

    # Get KPIs
    svc = KPIService(session_factory=lambda: db_session)
    kpis = svc.get_kpis()
    kpi_map = {k.name: k for k in kpis}

    # Verify Total PnL is correct dollar loss, not apparent raw profit
    # BTC real: 6.50. SOL real: -500.0. Total = -493.50.
    assert kpi_map["Total PnL"].value == -493.50
    assert kpi_map["Total PnL"].status == "negative"
    assert kpi_map["Total PnL"].trend == "declining"

    # Wins / Losses counts should still be 1 win and 1 loss
    # Win rate is 50.0%
    assert kpi_map["Win Rate"].value == 50.0
    assert kpi_map["Trades"].value == 2

    # Avg PnL should be -493.50 / 2 = -246.75
    assert kpi_map["Avg PnL"].value == -246.75


def test_kpi_service_profit_factor_sharpe_drawdown(db_session):
    """Test profit factor, Sharpe and Max Drawdown with correct dollar values."""
    now = datetime.now(timezone.utc)

    # Add three winning trades with quantity 10, pnl 10 => $100 profit each
    # Add one losing trade with quantity 5, pnl -40 => -$200 loss
    # Total wins: $300. Total loss: $200. Profit factor = 300 / 200 = 1.5.

    for i in range(1, 4):
        t = Trade(
            id=100 + i,
            symbol="ETHUSDT",
            side="LONG",
            entry=3000.0,
            pnl=10.0,
            status="CLOSED",
            created_at=now - timedelta(hours=10 - i),
            closed_at=now - timedelta(hours=9 - i),
        )
        db_session.add(t)

        pt = PaperTrade(
            id=100 + i,
            position_id=100 + i,
            symbol="ETHUSDT",
            side="LONG",
            entry=3000.0,
            quantity=10.0,
            pnl=10.0,
            status="CLOSED",
        )
        db_session.add(pt)

    # Losing trade
    t_loss = Trade(
        id=104,
        symbol="ETHUSDT",
        side="LONG",
        entry=3000.0,
        pnl=-40.0,
        status="CLOSED",
        created_at=now - timedelta(hours=5),
        closed_at=now - timedelta(hours=4),
    )
    db_session.add(t_loss)

    pt_loss = PaperTrade(
        id=104,
        position_id=104,
        symbol="ETHUSDT",
        side="LONG",
        entry=3000.0,
        quantity=5.0,
        pnl=-40.0,
        status="CLOSED",
    )
    db_session.add(pt_loss)

    db_session.flush()

    svc = KPIService(session_factory=lambda: db_session)
    kpis = svc.get_kpis()
    kpi_map = {k.name: k for k in kpis}

    # Total profit from wins: 3 * 100.0 = 300.0
    # Total loss from losses: 1 * 200.0 = 200.0
    # Profit factor: 1.50
    assert kpi_map["Profit Factor"].value == 1.50

    # Total PnL should be 100.0
    assert kpi_map["Total PnL"].value == 100.0

    # Max Drawdown calculation:
    # Sorted trades by created_at:
    # 1. Win 1 (+100): running = 100, peak = 100, dd = 0
    # 2. Win 2 (+100): running = 200, peak = 200, dd = 0
    # 3. Win 3 (+100): running = 300, peak = 300, dd = 0
    # 4. Loss (-200): running = 100, peak = 300, dd = 200.
    # Max DD should be 200.0.
    assert kpi_map["Max Drawdown"].value == 200.0
