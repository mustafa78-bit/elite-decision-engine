from __future__ import annotations

from datetime import UTC, datetime, timedelta

from database import PaperTrade, Signal, Trade
from services.timeline_service import TimelineService


def _make_trade_with_paper(session, trade_id, signal_id, symbol, side, entry, pnl, quantity, exit_price, now):
    trade = Trade(
        id=trade_id,
        signal_id=signal_id,
        symbol=symbol,
        side=side,
        entry=entry,
        pnl=pnl,
        exit_price=exit_price,
        status="CLOSED",
        close_reason="TP_HIT",
        created_at=now - timedelta(hours=2),
        closed_at=now - timedelta(hours=1),
    )
    session.add(trade)
    session.add(PaperTrade(
        id=trade_id,
        position_id=trade_id,
        symbol=symbol,
        side=side,
        entry=entry,
        exit_price=exit_price,
        quantity=quantity,
        pnl=pnl,
        status="CLOSED",
    ))
    return trade


def test_signal_timeline_real_dollar_pnl(db_session):
    now = datetime.now(UTC)
    signal = Signal(id=30, symbol="BTCUSDT", side="LONG", timeframe="1h", status="EXECUTED", created_at=now - timedelta(hours=3))
    db_session.add(signal)
    _make_trade_with_paper(db_session, 30, 30, "BTCUSDT", "LONG", 60000.0, 1000.0, 0.05, 61000.0, now)
    db_session.flush()

    svc = TimelineService(session_factory=lambda: db_session)
    events = svc.signal_timeline(30)

    closed_event = next(e for e in events if e["type"] == "trade_closed")
    assert closed_event["data"]["pnl"] == 50.0


def test_trade_timeline_real_dollar_pnl(db_session):
    now = datetime.now(UTC)
    _make_trade_with_paper(db_session, 31, None, "ETHUSDT", "SHORT", 3000.0, 50.0, 2.0, 2950.0, now)
    db_session.flush()

    svc = TimelineService(session_factory=lambda: db_session)
    events = svc.trade_timeline(31)

    closed_event = next(e for e in events if e["type"] == "trade_closed")
    assert closed_event["data"]["pnl"] == 100.0


def test_global_timeline_real_dollar_pnl(db_session):
    now = datetime.now(UTC)
    _make_trade_with_paper(db_session, 32, None, "SOLUSDT", "LONG", 150.0, 5.0, 10.0, 150.5, now)
    db_session.flush()

    svc = TimelineService(session_factory=lambda: db_session)
    result = svc.global_timeline(symbol="SOLUSDT")

    trade_event = next(e for e in result["events"] if e["type"] == "trade_closed")
    assert trade_event["pnl"] == 50.0


def test_trade_timeline_no_matching_paper_trade_falls_back_to_quantity_one(db_session):
    now = datetime.now(UTC)
    trade = Trade(
        id=33,
        symbol="DOGEUSDT",
        side="LONG",
        entry=0.15,
        pnl=0.01,
        status="CLOSED",
        close_reason="TP_HIT",
        created_at=now - timedelta(hours=2),
        closed_at=now - timedelta(hours=1),
    )
    db_session.add(trade)
    db_session.flush()

    svc = TimelineService(session_factory=lambda: db_session)
    events = svc.trade_timeline(33)

    closed_event = next(e for e in events if e["type"] == "trade_closed")
    assert closed_event["data"]["pnl"] == 0.01
