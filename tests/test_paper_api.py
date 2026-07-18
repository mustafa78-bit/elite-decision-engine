"""Integration tests for the Paper Trading REST API.

Uses ``api_client`` (which patches ``database.get_session``) and
``db_session`` for seeding test data.
"""

import logging

logging.getLogger("httpx2").setLevel(logging.WARNING)

from datetime import datetime, timezone

from database import (
    CANCEL,
    CLOSED,
    FILLED,
    OPEN,
    PENDING,
    STOP_LOSS,
    TAKE_PROFIT,
    PaperOrder,
    PaperTrade,
    Trade,
)


def _make_paper_order(db_session, **overrides):
    kwargs = dict(
        symbol="BTCUSDT",
        side="LONG",
        order_type="MARKET",
        quantity=1.0,
        price=50000.0,
        filled_price=None,
        filled_quantity=None,
        status=PENDING,
        trade_id=None,
    )
    kwargs.update(overrides)
    o = PaperOrder(**kwargs)
    db_session.add(o)
    db_session.flush()
    return o


def _make_paper_trade(db_session, **overrides):
    kwargs = dict(
        position_id=1,
        order_id=1,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        quantity=1.0,
        pnl=0.0,
        status=OPEN,
    )
    kwargs.update(overrides)
    t = PaperTrade(**kwargs)
    db_session.add(t)
    db_session.flush()
    return t


def _make_trade(db_session, **overrides):
    kwargs = dict(
        signal_id=1,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49250.0,
        tp1=51000.0,
        status=OPEN,
    )
    kwargs.update(overrides)
    t = Trade(**kwargs)
    db_session.add(t)
    db_session.flush()
    return t


# ── GET /paper/orders ───────────────────────────────────────────────────────


def test_list_orders_empty(api_client):
    resp = api_client.get("/paper/orders")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"orders": [], "total": 0, "offset": 0, "limit": 50}


def test_list_orders_with_data(api_client, db_session):
    _make_paper_order(db_session, symbol="BTCUSDT")
    _make_paper_order(db_session, symbol="ETHUSDT", status=FILLED)
    resp = api_client.get("/paper/orders")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["orders"]) == 2


def test_list_orders_filter_by_symbol(api_client, db_session):
    _make_paper_order(db_session, symbol="BTCUSDT")
    _make_paper_order(db_session, symbol="ETHUSDT")
    resp = api_client.get("/paper/orders?symbol=BTCUSDT")
    body = resp.json()
    assert body["total"] == 1
    assert body["orders"][0]["symbol"] == "BTCUSDT"


def test_list_orders_filter_by_status(api_client, db_session):
    _make_paper_order(db_session, status=PENDING)
    _make_paper_order(db_session, status=FILLED)
    resp = api_client.get("/paper/orders?status=FILLED")
    body = resp.json()
    assert body["total"] == 1
    assert body["orders"][0]["status"] == "FILLED"


def test_list_orders_filter_by_side(api_client, db_session):
    _make_paper_order(db_session, side="LONG")
    _make_paper_order(db_session, side="SHORT")
    resp = api_client.get("/paper/orders?side=SHORT")
    body = resp.json()
    assert body["total"] == 1
    assert body["orders"][0]["side"] == "SHORT"


def test_list_orders_pagination(api_client, db_session):
    for i in range(5):
        _make_paper_order(db_session, symbol=f"PAIR{i}")
    resp = api_client.get("/paper/orders?limit=2&offset=0")
    body = resp.json()
    assert len(body["orders"]) == 2
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 0

    resp2 = api_client.get("/paper/orders?limit=2&offset=2")
    body2 = resp2.json()
    assert len(body2["orders"]) == 2


def test_list_orders_invalid_status_returns_422(api_client):
    resp = api_client.get("/paper/orders?status=INVALID")
    assert resp.status_code == 422


# ── GET /paper/orders/{id} ──────────────────────────────────────────────────


def test_get_order_found(api_client, db_session):
    o = _make_paper_order(db_session)
    resp = api_client.get(f"/paper/orders/{o.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == o.id
    assert body["symbol"] == "BTCUSDT"


def test_get_order_not_found(api_client):
    resp = api_client.get("/paper/orders/99999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ── GET /paper/trades ───────────────────────────────────────────────────────


def test_list_trades_empty(api_client):
    resp = api_client.get("/paper/trades")
    body = resp.json()
    assert body == {"trades": [], "total": 0, "offset": 0, "limit": 50}


def test_list_trades_with_data(api_client, db_session):
    _make_paper_trade(db_session)
    _make_paper_trade(db_session, position_id=2, order_id=2)
    resp = api_client.get("/paper/trades")
    body = resp.json()
    assert body["total"] == 2


def test_list_trades_filter_by_symbol(api_client, db_session):
    _make_paper_trade(db_session, symbol="BTCUSDT")
    _make_paper_trade(db_session, symbol="ETHUSDT", position_id=2, order_id=2)
    resp = api_client.get("/paper/trades?symbol=ETHUSDT")
    body = resp.json()
    assert body["total"] == 1
    assert body["trades"][0]["symbol"] == "ETHUSDT"


def test_list_trades_filter_by_status(api_client, db_session):
    _make_paper_trade(db_session, status=OPEN)
    _make_paper_trade(db_session, position_id=2, order_id=2, status=TAKE_PROFIT)
    resp = api_client.get("/paper/trades?status=TAKE_PROFIT")
    body = resp.json()
    assert body["total"] == 1
    assert body["trades"][0]["status"] == "TAKE_PROFIT"


def test_list_trades_filter_by_side(api_client, db_session):
    _make_paper_trade(db_session, side="LONG")
    _make_paper_trade(db_session, position_id=2, order_id=2, side="SHORT")
    resp = api_client.get("/paper/trades?side=SHORT")
    body = resp.json()
    assert body["total"] == 1
    assert body["trades"][0]["side"] == "SHORT"


def test_list_trades_pagination(api_client, db_session):
    for i in range(5):
        _make_paper_trade(db_session, position_id=i + 1, order_id=i + 1)
    resp = api_client.get("/paper/trades?limit=2&offset=0")
    body = resp.json()
    assert len(body["trades"]) == 2
    assert body["total"] == 5


# ── GET /paper/trades/{id} ──────────────────────────────────────────────────


def test_get_trade_found(api_client, db_session):
    t = _make_paper_trade(db_session)
    resp = api_client.get(f"/paper/trades/{t.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == t.id


def test_get_trade_not_found(api_client):
    resp = api_client.get("/paper/trades/99999")
    assert resp.status_code == 404


# ── GET /paper/positions ────────────────────────────────────────────────────


def test_list_positions_empty(api_client):
    resp = api_client.get("/paper/positions")
    body = resp.json()
    assert body == {"positions": [], "total": 0, "offset": 0, "limit": 50}


def test_list_positions_with_data(api_client, db_session):
    _make_trade(db_session)
    _make_trade(db_session, signal_id=2)
    resp = api_client.get("/paper/positions")
    body = resp.json()
    assert body["total"] == 2


def test_list_positions_filter_by_status(api_client, db_session):
    _make_trade(db_session, status=OPEN)
    _make_trade(db_session, signal_id=2, status=CLOSED)
    resp = api_client.get("/paper/positions?status=OPEN")
    body = resp.json()
    assert body["total"] == 1
    assert body["positions"][0]["status"] == "OPEN"


# ── GET /paper/summary ──────────────────────────────────────────────────────


def test_summary_empty(api_client):
    resp = api_client.get("/paper/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["orders"]["total"] == 0
    assert body["trades"]["total"] == 0
    assert body["positions"]["total"] == 0


def test_summary_with_data(api_client, db_session):
    _make_paper_order(db_session, status=PENDING)
    _make_paper_order(db_session, status=FILLED)
    _make_paper_order(db_session, status=CANCEL)

    _make_paper_trade(db_session, status=OPEN)
    _make_paper_trade(db_session, position_id=2, order_id=2, pnl=100.0, status=TAKE_PROFIT)
    _make_paper_trade(db_session, position_id=3, order_id=3, pnl=-50.0, status=STOP_LOSS)

    _make_trade(db_session, status=OPEN)
    _make_trade(db_session, signal_id=2, status=CLOSED)

    resp = api_client.get("/paper/summary")
    body = resp.json()

    assert body["orders"]["total"] == 3
    assert body["orders"]["pending"] == 1
    assert body["orders"]["filled"] == 1
    assert body["orders"]["cancelled"] == 1

    assert body["trades"]["total"] == 3
    assert body["trades"]["open"] == 1
    assert body["trades"]["closed"] == 2

    assert body["positions"]["total"] == 2
    assert body["positions"]["open"] == 1

    assert body["performance"]["winning_trades"] == 1
    assert body["performance"]["losing_trades"] == 1
    assert body["performance"]["win_rate"] == 50.0
    assert body["performance"]["total_pnl"] == 50.0
