"""API route tests for the Elite Decision Engine FastAPI application.

Uses the ``api_client`` fixture from ``conftest.py`` which patches
``database.get_session`` before routes are imported, so every route that
reads or writes the database uses the test SQLite database.

Verifies status codes, response shapes, and error handling for every
DB-backed REST endpoint.  Routes that depend on external APIs (Hyperliquid
collector, exchange connectors) test their failure fallback paths.
"""

from datetime import datetime, timezone

from auth.jwt import create_access_token
from database import JournalEntry, Notification, Signal, Trade


def _make_signal(db_session, **overrides):
    kwargs = dict(
        symbol="BTCUSDT",
        side="LONG",
        timeframe="1h",
        status="OPEN",
        confidence=85.0,
        score=0.85,
    )
    kwargs.update(overrides)
    s = Signal(**kwargs)
    db_session.add(s)
    db_session.flush()
    return s


def _make_trade(db_session, signal_id=1, status="OPEN", pnl=None, **overrides):
    if signal_id is not None:
        existing_signal = db_session.query(Signal).filter(Signal.id == signal_id).first()
        if not existing_signal:
            sig = Signal(id=signal_id, symbol=overrides.get("symbol", "BTCUSDT"), side=overrides.get("side", "LONG"))
            db_session.add(sig)
            db_session.flush()
    kwargs = dict(
        signal_id=signal_id,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49250.0,
        tp1=51000.0,
        tp2=52000.0,
        rr=2.0,
        status=status,
        pnl=pnl,
    )
    kwargs.update(overrides)
    t = Trade(**kwargs)
    db_session.add(t)
    db_session.flush()
    return t


def _make_notification(db_session, **overrides):
    kwargs = dict(event_type="trade_opened", payload={}, read=False)
    kwargs.update(overrides)
    n = Notification(**kwargs)
    db_session.add(n)
    db_session.flush()
    return n


def _make_user(db_session, **overrides):
    from auth.service import hash_password
    kwargs = dict(username="testuser", email="test@example.com", hashed_password=hash_password("pass123"))
    kwargs.update(overrides)
    from database import User
    u = User(**kwargs)
    db_session.add(u)
    db_session.flush()
    return u


def _token_for_user(user) -> str:
    return create_access_token({"sub": str(user.id), "username": user.username})


# ─── Health ────────────────────────────────────────────────────────────────


def test_get_health(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "elite-decision-engine"


# ─── Monitoring ────────────────────────────────────────────────────────────


def test_get_monitoring_empty(api_client):
    resp = api_client.get("/monitoring")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"]["status"] in ("connected", "error")
    assert body["engines"]["trade_count"]["total"] == 0
    assert body["engines"]["signal_count"] == 0


def test_get_monitoring_with_data(api_client, db_session):
    _make_signal(db_session)
    _make_trade(db_session, signal_id=1)
    resp = api_client.get("/monitoring")
    assert resp.status_code == 200
    body = resp.json()
    assert body["engines"]["signal_count"] == 1
    assert body["engines"]["trade_count"]["total"] == 1
    assert body["engines"]["trade_count"]["open"] == 1


# ─── Notifications ─────────────────────────────────────────────────────────


def test_get_notifications_empty(api_client):
    resp = api_client.get("/notifications")
    assert resp.status_code == 200
    body = resp.json()
    assert body["notifications"] == []
    assert body["total"] == 0


def test_get_notifications_with_data(api_client, db_session):
    _make_notification(db_session, event_type="test_event")
    resp = api_client.get("/notifications")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["notifications"]) == 1
    assert body["notifications"][0]["event_type"] == "test_event"
    assert body["notifications"][0]["read"] is False


def test_mark_notification_read(api_client, db_session):
    n = _make_notification(db_session)
    resp = api_client.put(f"/notifications/{n.id}/read")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_mark_notification_read_missing(api_client):
    resp = api_client.put("/notifications/99999/read")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ─── Paper Trading ─────────────────────────────────────────────────────────


def test_get_paper_trading_empty(api_client):
    resp = api_client.get("/paper-trading")
    assert resp.status_code == 200
    body = resp.json()
    assert body["open"] == []
    assert body["closed"] == []
    assert body["performance"]["total_trades"] == 0


def test_get_paper_trading_with_trades(api_client, db_session):
    _make_trade(db_session, signal_id=1, status="OPEN")
    _make_trade(
        db_session, signal_id=2, status="TP_HIT", pnl=500.0,
        exit_price=51000.0, close_reason="TP_HIT",
    )
    resp = api_client.get("/paper-trading")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["open"]) == 1
    assert len(body["closed"]) == 1
    assert body["performance"]["total_trades"] == 2
    assert body["performance"]["winning_trades"] == 1
    assert body["performance"]["total_pnl"] == 500.0


def test_get_paper_trading_scoped_to_owning_user(api_client, db_session):
    _make_trade(db_session, signal_id=1, symbol="BTCUSDT", status="OPEN", user_id=1)
    _make_trade(db_session, signal_id=2, symbol="ETHUSDT", status="OPEN", user_id=2)

    resp = api_client.get("/paper-trading")
    symbols = {t["symbol"] for t in resp.json()["open"]}
    assert symbols == {"BTCUSDT"}

    other_user_token = create_access_token({"sub": "2", "username": "other"})
    resp2 = api_client.get("/paper-trading", headers={"Authorization": f"Bearer {other_user_token}"})
    symbols2 = {t["symbol"] for t in resp2.json()["open"]}
    assert symbols2 == {"ETHUSDT"}


def test_get_paper_trading_mixed_quantities(api_client, db_session):
    from database import PaperTrade

    # 1. Open trade with no matching PaperTrade (falls back to Trade.pnl)
    _make_trade(db_session, id=10, signal_id=1, status="OPEN", pnl=10.0)

    # 2. Closed trade: entry $3,000, exit $3,050 (pnl $50 per unit), quantity 0.2
    # Real dollar PnL = $50 * 0.2 = $10.0
    t2 = _make_trade(
        db_session, id=11, signal_id=2, status="CLOSED", pnl=50.0,
        entry=3000.0, exit_price=3050.0,
    )
    db_session.add(PaperTrade(
        position_id=t2.id,
        symbol="BTCUSDT",
        side="LONG",
        entry=3000.0,
        exit_price=3050.0,
        quantity=0.2,
        pnl=50.0,
        status="CLOSED",
    ))

    # 3. Closed trade: entry $100, exit $90 (pnl -$10 per unit), quantity 5.0
    # Real dollar PnL = -$10 * 5.0 = -$50.0
    t3 = _make_trade(
        db_session, id=12, signal_id=3, status="CLOSED", pnl=-10.0,
        entry=100.0, exit_price=90.0,
    )
    db_session.add(PaperTrade(
        position_id=t3.id,
        symbol="ETHUSDT",
        side="LONG",
        entry=100.0,
        exit_price=90.0,
        quantity=5.0,
        pnl=-10.0,
        status="CLOSED",
    ))

    # 4. Closed trade with no matching PaperTrade (falls back to Trade.pnl, quantity=1.0)
    # Real dollar PnL = -$5.0
    _make_trade(
        db_session, id=13, signal_id=4, status="CLOSED", pnl=-5.0,
        entry=150.0, exit_price=145.0,
    )

    db_session.flush()

    resp = api_client.get("/paper-trading")
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["open"]) == 1
    assert body["open"][0]["id"] == 10
    assert body["open"][0]["pnl"] == 10.0  # falls back to Trade.pnl

    assert len(body["closed"]) == 3
    closed_by_id = {item["id"]: item for item in body["closed"]}

    # Trade 11: real dollar pnl = 50.0 * 0.2 = 10.0
    assert closed_by_id[11]["pnl"] == 10.0
    # Trade 12: real dollar pnl = -10.0 * 5.0 = -50.0
    assert closed_by_id[12]["pnl"] == -50.0
    # Trade 13: fallback (no PaperTrade) -> raw pnl -5.0
    assert closed_by_id[13]["pnl"] == -5.0

    # Total: 10.0 + (-50.0) + (-5.0) = -45.0
    assert body["performance"]["total_pnl"] == -45.0


# ─── Execution Status ──────────────────────────────────────────────────────


def test_get_execution_status(api_client, db_session):
    _make_signal(db_session, status="OPEN", confidence=85.0)
    _make_signal(db_session, status="EXECUTED", confidence=92.0)
    _make_signal(db_session, status="REJECTED", confidence=40.0)
    _make_trade(db_session, signal_id=1, status="OPEN")
    _make_trade(db_session, signal_id=2, status="TP_HIT", pnl=300.0)
    resp = api_client.get("/execution/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["signals"]["total"] == 3
    assert body["signals"]["approved"] == 2
    assert body["signals"]["rejected"] == 1
    assert body["trades"]["total"] == 2
    assert body["trades"]["open"] == 1
    assert body["trades"]["tp_hit"] == 1


# ─── Signals Ranking ───────────────────────────────────────────────────────


def test_get_signals_ranking_empty(api_client):
    resp = api_client.get("/signals/ranking")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_signals_ranking_with_data(api_client, db_session):
    _make_signal(db_session, confidence=95.0, score=0.95, status="OPEN")
    _make_signal(db_session, confidence=60.0, score=0.50, status="REJECTED")
    resp = api_client.get("/signals/ranking")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["rank"] == 1
    assert data[0]["decision"] == "STRONG_APPROVE"
    assert data[1]["rank"] == 2
    assert data[1]["decision"] == "REJECT"


# ─── Journal ───────────────────────────────────────────────────────────────


def test_list_journal_empty(api_client):
    resp = api_client.get("/journal")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_journal(api_client):
    payload = {
        "symbol": "BTCUSDT",
        "side": "LONG",
        "entry_price": 50000.0,
        "result": "WIN",
        "pnl": 1000.0,
    }
    create_resp = api_client.post("/journal", json=payload)
    assert create_resp.status_code == 200
    entry_id = create_resp.json().get("id")
    assert entry_id is not None

    list_resp = api_client.get("/journal")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert len(data) == 1
    assert data[0]["id"] == entry_id
    assert data[0]["symbol"] == "BTCUSDT"
    assert data[0]["pnl"] == 1000.0


def test_update_journal(api_client):
    payload = {
        "symbol": "ETHUSDT",
        "side": "SHORT",
        "entry_price": 3000.0,
        "result": "PENDING",
    }
    create_resp = api_client.post("/journal", json=payload)
    entry_id = create_resp.json()["id"]

    update_payload = {
        "result": "LOSS",
        "pnl": -150.0,
        "exit_reason": "SL_HIT",
    }
    update_resp = api_client.put(f"/journal/{entry_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "updated"

    list_resp = api_client.get("/journal")
    entry = list_resp.json()[0]
    assert entry["result"] == "LOSS"
    assert entry["pnl"] == -150.0


def test_delete_journal(api_client):
    payload = {
        "symbol": "SOLUSDT",
        "side": "LONG",
        "entry_price": 100.0,
    }
    create_resp = api_client.post("/journal", json=payload)
    entry_id = create_resp.json()["id"]

    delete_resp = api_client.delete(f"/journal/{entry_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"

    list_resp = api_client.get("/journal")
    assert list_resp.json() == []


def test_update_journal_missing(api_client):
    resp = api_client.put("/journal/99999", json={"result": "WIN"})
    assert resp.status_code == 404
    assert "not found" in resp.json().get("detail", "").lower()


def test_delete_journal_missing(api_client):
    resp = api_client.delete("/journal/99999")
    assert resp.status_code == 404
    assert "not found" in resp.json().get("detail", "").lower()


def test_another_user_cannot_read_update_or_delete_this_journal_entry(api_client):
    # api_client is authenticated as user_id=1 (see conftest.py's api_client fixture)
    payload = {"symbol": "BTCUSDT", "side": "LONG", "entry_price": 50000.0}
    create_resp = api_client.post("/journal", json=payload)
    entry_id = create_resp.json()["id"]

    other_user_token = create_access_token({"sub": "2", "username": "other"})
    headers = {"Authorization": f"Bearer {other_user_token}"}

    # GET /journal is list-only (no get-by-id) -- prove it via the list, not
    # a per-id read.
    other_list = api_client.get("/journal", headers=headers)
    assert other_list.status_code == 200
    assert entry_id not in {row["id"] for row in other_list.json()}

    assert api_client.put(
        f"/journal/{entry_id}", json={"result": "WIN"}, headers=headers
    ).status_code == 404
    assert api_client.delete(f"/journal/{entry_id}", headers=headers).status_code == 404

    # Confirm it's genuinely untouched, not silently modified.
    still_there = api_client.get("/journal").json()
    assert len(still_there) == 1
    assert still_there[0]["id"] == entry_id
    assert still_there[0]["result"] == "PENDING"


def test_journal_entry_with_no_owner_visible_and_editable_by_everyone(api_client, db_session):
    # TradeMemory.record() creates JournalEntry rows as a side effect of
    # opening a paper trade with no signal (no owning user to inherit) --
    # these must stay visible/editable by every authenticated user, same
    # NULL-fallback contract as Signal/Trade.
    entry = JournalEntry(symbol="ETHUSDT", side="LONG", entry_price=3000.0, user_id=None)
    db_session.add(entry)
    db_session.flush()

    other_user_token = create_access_token({"sub": "2", "username": "other"})
    headers = {"Authorization": f"Bearer {other_user_token}"}

    resp = api_client.get("/journal", headers=headers)
    assert entry.id in {row["id"] for row in resp.json()}

    update_resp = api_client.put(f"/journal/{entry.id}", json={"result": "WIN"}, headers=headers)
    assert update_resp.status_code == 200


# ─── Backtest ──────────────────────────────────────────────────────────────


def test_get_backtest_empty(api_client):
    resp = api_client.get("/backtest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["total_signals"] == 0
    assert body["trades"]["total"] == 0


def test_get_backtest_with_data(api_client, db_session):
    _make_signal(db_session, id=1, status="EXECUTED", approved=True, confidence=90.0)
    _make_signal(db_session, id=2, status="REJECTED", approved=False, confidence=30.0)
    _make_signal(db_session, id=3, status="CANCELLED", approved=False, confidence=10.0)
    _make_trade(db_session, signal_id=1, status="TP_HIT", pnl=500.0)
    _make_trade(db_session, signal_id=2, status="SL_HIT", pnl=-200.0)
    _make_trade(db_session, signal_id=3, status="CANCEL", pnl=0.0)
    resp = api_client.get("/backtest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["total_signals"] == 3
    assert body["summary"]["approved_signals"] == 1
    assert body["trades"]["total"] == 3
    assert body["trades"]["closed"] == 3
    assert body["trades"]["wins"] == 1
    assert body["trades"]["losses"] == 1
    assert body["performance"]["total_pnl"] == 300.0
    assert body["performance"]["win_rate_pct"] == 50.0
    assert body["performance"]["avg_win"] == 500.0
    assert body["performance"]["avg_loss"] == 200.0
    assert body["performance"]["profit_factor"] == 2.5
    assert body["performance"]["max_drawdown"] == 200.0


def test_get_backtest_mixed_quantities(api_client, db_session):
    from database import PaperTrade

    _make_signal(db_session, id=1, status="EXECUTED", approved=True, confidence=90.0)
    _make_signal(db_session, id=2, status="EXECUTED", approved=True, confidence=90.0)

    # Trade A: raw per-unit pnl 500.0, quantity 0.1 -> real dollar pnl 50.0
    t1 = _make_trade(db_session, signal_id=1, status="TP_HIT", pnl=500.0)
    db_session.add(PaperTrade(
        position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, exit_price=55000.0, quantity=0.1, pnl=500.0, status="CLOSED",
    ))

    # Trade B: raw per-unit pnl -200.0, quantity 2.0 -> real dollar pnl -400.0
    t2 = _make_trade(db_session, signal_id=2, status="SL_HIT", pnl=-200.0)
    db_session.add(PaperTrade(
        position_id=t2.id, symbol="ETHUSDT", side="LONG",
        entry=3000.0, exit_price=2800.0, quantity=2.0, pnl=-200.0, status="CLOSED",
    ))
    db_session.flush()

    resp = api_client.get("/backtest")
    assert resp.status_code == 200
    body = resp.json()

    # Real dollar pnls: [50.0, -400.0] -> total -350.0
    assert body["performance"]["total_pnl"] == -350.0
    assert body["performance"]["roi_pct"] == -87.5
    assert body["performance"]["avg_win"] == 50.0
    assert body["performance"]["avg_loss"] == 400.0
    assert body["performance"]["profit_factor"] == 0.12
    assert body["performance"]["max_drawdown"] == 400.0
    assert body["performance"]["sharpe_ratio"] == -0.55

    # Sign-based counts are unaffected by quantity
    assert body["trades"]["wins"] == 1
    assert body["trades"]["losses"] == 1
    assert body["performance"]["win_rate_pct"] == 50.0


# ─── Intelligence (DB fallback when market data unavailable) ───────────────


def test_get_intelligence_db_fallback(api_client, db_session):
    _make_signal(db_session, status="OPEN")
    resp = api_client.get("/intelligence")
    assert resp.status_code == 200
    body = resp.json()
    assert "market" in body
    assert body["signals"]["total"] == 1
    assert body["trades"]["open"] == 0


# ─── Trading Control (exchange connectors created, DB queries work) ────────


def test_get_trading_control(api_client, db_session):
    _make_signal(db_session, status="OPEN", approved=False)
    _make_trade(db_session, signal_id=1, status="OPEN")
    resp = api_client.get("/trading-control")
    assert resp.status_code == 200
    body = resp.json()
    assert body["signals"]["total"] == 1
    assert body["trades"]["total"] == 1
    assert body["trades"]["open"] == 1
    assert len(body["exchanges"]) == 2


# ─── Signals (functional) ────────────────────────────────────────────────


def test_get_signals_with_data(api_client, db_session):
    _make_signal(db_session, confidence=85.0, score=0.85, status="OPEN")
    resp = api_client.get("/signals")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "BTCUSDT"
    assert data[0]["confidence"] == 85.0
    assert data[0]["decision"] == "APPROVE"
    assert data[0]["status"] == "OPEN"


def test_get_signals_scoped_to_owning_user(api_client, db_session):
    # api_client is authenticated as user_id=1 (see conftest.py's api_client fixture)
    _make_signal(db_session, symbol="BTCUSDT", user_id=1)
    _make_signal(db_session, symbol="ETHUSDT", user_id=2)

    resp = api_client.get("/signals")
    assert resp.status_code == 200
    symbols = {row["symbol"] for row in resp.json()}
    assert symbols == {"BTCUSDT"}

    other_user_token = create_access_token({"sub": "2", "username": "other"})
    resp2 = api_client.get("/signals", headers={"Authorization": f"Bearer {other_user_token}"})
    assert resp2.status_code == 200
    symbols2 = {row["symbol"] for row in resp2.json()}
    assert symbols2 == {"ETHUSDT"}


def test_get_signals_null_owner_visible_to_everyone(api_client, db_session):
    # Background-job-created signals (the scanner) have no owning user --
    # NULL user_id, must stay visible to every authenticated user.
    _make_signal(db_session, symbol="SOLUSDT", user_id=None)

    resp = api_client.get("/signals")
    assert resp.status_code == 200
    assert {row["symbol"] for row in resp.json()} == {"SOLUSDT"}

    other_user_token = create_access_token({"sub": "2", "username": "other"})
    resp2 = api_client.get("/signals", headers={"Authorization": f"Bearer {other_user_token}"})
    assert resp2.status_code == 200
    assert {row["symbol"] for row in resp2.json()} == {"SOLUSDT"}


# ─── Risk (functional) ────────────────────────────────────────────────────


def test_get_risk_with_trades(api_client, db_session):
    _make_trade(db_session, signal_id=1, status="OPEN", entry=50000.0, pnl=0.0)
    _make_trade(db_session, signal_id=2, status="TP_HIT", entry=51000.0, pnl=500.0)
    headers = {"Authorization": f"Bearer {_token_for_user(_make_user(db_session))}"}
    resp = api_client.get("/risk", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["open_trades"] == 1
    assert body["max_open_trades"] == 3
    assert "BTCUSDT" in body["symbol_exposure"]
    assert body["portfolio_exposure"] > 0
    assert body["risk_score"] is not None


def test_get_risk_daily_loss_with_naive_closed_at(api_client, db_session):
    # SQLite returns naive datetimes for Trade.closed_at regardless of the
    # column's DateTime(timezone=True) declaration -- confirmed live
    # 2026-08-20: /risk 500'd on every request that had a closed, losing
    # trade because it compared this naive value against an
    # aware datetime.now(UTC) today_start.
    _make_trade(
        db_session, signal_id=1, status="TP_HIT", entry=50000.0, pnl=-500.0,
        closed_at=datetime.now(),
    )
    headers = {"Authorization": f"Bearer {_token_for_user(_make_user(db_session))}"}
    resp = api_client.get("/risk", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["daily_loss"] == -500.0


# ─── Position Sizing (functional) ──────────────────────────────────────────


def test_get_position_sizing(api_client, db_session):
    headers = {"Authorization": f"Bearer {_token_for_user(_make_user(db_session))}"}
    resp = api_client.get("/position-sizing?entry=50000&atr=500", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["quantity"] > 0
    assert body["notional_value"] > 0
    assert body["risk_amount"] > 0


# ─── Portfolio (empty) ─────────────────────────────────────────────────────


def test_get_portfolio_empty(api_client, db_session):
    headers = {"Authorization": f"Bearer {_token_for_user(_make_user(db_session))}"}
    resp = api_client.get("/portfolio", headers=headers)
    assert resp.status_code == 200


# ─── Performance (empty) ───────────────────────────────────────────────────


def test_get_performance_empty(api_client, db_session):
    headers = {"Authorization": f"Bearer {_token_for_user(_make_user(db_session))}"}
    resp = api_client.get("/performance", headers=headers)
    assert resp.status_code == 200


# ─── Market error fallback ──────────────────────────────────────────────────


def test_get_market(api_client):
    resp = api_client.get("/market")
    assert resp.status_code == 200
    body = resp.json()
    if "error" in body:
        assert isinstance(body["error"], str)
    else:
        assert "symbol" in body
        assert "price" in body


# ─── Users/me (auth) ────────────────────────────────────────────────────────


def test_get_users_me_with_auth(api_client, db_session):
    user = _make_user(db_session)
    headers = {"Authorization": f"Bearer {_token_for_user(user)}"}
    resp = api_client.get("/users/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "testuser"
    assert body["email"] == "test@example.com"
    # Powers Profile.tsx's "member since" field -- previously absent, the
    # page always showed a hardcoded "unavailable" for it.
    assert body["created_at"] is not None


def test_get_users_me_no_auth():
    from fastapi.testclient import TestClient

    from api.main import app
    client = TestClient(app)
    resp = client.get("/users/me")
    assert resp.status_code == 401


# ─── Users/settings (auth) ──────────────────────────────────────────────────


def test_get_users_settings_with_auth(api_client, db_session):
    user = _make_user(db_session)
    headers = {"Authorization": f"Bearer {_token_for_user(user)}"}
    resp = api_client.get("/users/settings", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["timezone"] == "UTC"


def test_update_users_settings_with_auth(api_client, db_session):
    user = _make_user(db_session)
    headers = {"Authorization": f"Bearer {_token_for_user(user)}"}
    resp = api_client.put("/users/settings", json={"timezone": "America/New_York"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["settings"]["timezone"] == "America/New_York"


# ─── Regime ──────────────────────────────────────────────────────────────────


def test_get_regime(api_client):
    resp = api_client.get("/regime")
    assert resp.status_code == 200
    body = resp.json()
    if "error" in body:
        assert isinstance(body["error"], str)
    else:
        assert "regime" in body
        assert "trend" in body
        assert "volatility_state" in body
        assert "rsi" in body


# ─── Intelligence (success path with trades) ─────────────────────────────────


def test_get_intelligence_with_trades(api_client, db_session):
    _make_signal(db_session, status="OPEN")
    _make_signal(db_session, status="EXECUTED")
    _make_trade(db_session, signal_id=1, status="OPEN")
    _make_trade(db_session, signal_id=2, status="TP_HIT", pnl=500.0)
    resp = api_client.get("/intelligence")
    assert resp.status_code == 200
    body = resp.json()
    assert body["signals"]["total"] == 2
    assert body["signals"]["open"] == 1
    assert body["trades"]["open"] == 1
    assert body["trades"]["closed"] == 1
    assert body["trades"]["total_pnl"] == 500.0
    assert body["risk"]["open_trades"] == 1


# ─── Trading Control (detailed shape) ────────────────────────────────────────


def test_get_trading_control_shapes(api_client, db_session):
    _make_signal(db_session, status="OPEN", approved=False)
    _make_trade(db_session, signal_id=1, status="OPEN")
    resp = api_client.get("/trading-control")
    assert resp.status_code == 200
    body = resp.json()
    assert "exchanges" in body
    assert "shadow" in body
    assert body["shadow"]["mode"] == "active"
    for ex in body["exchanges"]:
        assert "name" in ex
        assert "trading_enabled" in ex
        assert "status" in ex
    assert "risk" in body
    assert body["risk"]["max_open_trades"] == 3


# ─── Market Live (response shape) ────────────────────────────────────────────


def test_get_market_live_response(api_client):
    resp = api_client.get("/market/live")
    assert resp.status_code == 200
    body = resp.json()
    if "error" in body:
        assert isinstance(body["error"], str)
    else:
        assert "symbol" in body
        assert "price" in body
        assert "candles" in body
        assert "timestamp" in body


# ─── Signals Ranking (all response fields) ────────────────────────────────────


def test_get_signals_ranking_fields(api_client, db_session):
    _make_signal(db_session, confidence=95.0, score=0.95, status="OPEN",
                 side="LONG", symbol="BTCUSDT", timeframe="1h")
    _make_signal(db_session, confidence=60.0, score=0.50, status="REJECTED",
                 side="SHORT", symbol="ETHUSDT", timeframe="1h")
    resp = api_client.get("/signals/ranking")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    for entry in data:
        assert "rank" in entry
        assert "id" in entry
        assert "symbol" in entry
        assert "side" in entry
        assert "timeframe" in entry
        assert "score" in entry
        assert "confidence" in entry
        assert "decision" in entry
        assert "trend_score" in entry
        assert "volume_score" in entry
        assert "btc_score" in entry
        assert "risk_score" in entry
        assert "status" in entry
    assert data[0]["rank"] == 1
    assert data[0]["decision"] == "STRONG_APPROVE"
    assert data[1]["rank"] == 2
    assert data[1]["decision"] == "REJECT"
    assert data[0]["side"] == "LONG"
    assert data[1]["side"] == "SHORT"


# ─── Position Sizing missing params ──────────────────────────────────────────


def test_get_position_sizing_missing_entry(api_client, db_session):
    headers = {"Authorization": f"Bearer {_token_for_user(_make_user(db_session))}"}
    resp = api_client.get("/position-sizing?atr=500", headers=headers)
    assert resp.status_code == 422


# ─── Auth register missing fields ─────────────────────────────────────────────


def test_register_missing_fields(api_client):
    resp = api_client.post("/auth/register", json={"username": "onlyuser"})
    assert resp.status_code == 422


# ─── Protected routes (require auth) ───────────────────────────────────────


def test_get_signals_requires_auth():
    from fastapi.testclient import TestClient

    from api.main import app
    client = TestClient(app)
    resp = client.get("/signals")
    assert resp.status_code == 401


def test_get_risk_requires_auth():
    from fastapi.testclient import TestClient

    from api.main import app
    client = TestClient(app)
    resp = client.get("/risk")
    assert resp.status_code == 401


def test_get_portfolio_requires_auth():
    from fastapi.testclient import TestClient

    from api.main import app
    client = TestClient(app)
    resp = client.get("/portfolio")
    assert resp.status_code == 401


def test_get_performance_requires_auth():
    from fastapi.testclient import TestClient

    from api.main import app
    client = TestClient(app)
    resp = client.get("/performance")
    assert resp.status_code == 401


def test_get_position_sizing_requires_auth():
    from fastapi.testclient import TestClient

    from api.main import app
    client = TestClient(app)
    resp = client.get("/position-sizing")
    assert resp.status_code == 401


def test_global_exception_handler_returns_json(api_client):
    resp = api_client.get("/nonexistent-route-that-404s")
    assert resp.status_code == 404
    assert resp.headers["content-type"] == "application/json"


def test_health_endpoint_returns_uptime(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["uptime_seconds"] >= 0
    assert "X-Request-ID" in resp.headers


def test_health_details_returns_all_components(api_client):
    resp = api_client.get("/health/details")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "uptime_seconds" in data
    assert "database" in data
    assert "collector" in data
    assert "cache" in data
    assert "execution" in data
    assert "dependencies" in data
    assert "errors" in data
    assert "metrics" in data
    assert "config" in data
    assert data["environment"] in ("development", "production", "test")
    assert "X-Request-ID" in resp.headers


def test_monitoring_returns_execution_and_deps(api_client):
    resp = api_client.get("/monitoring")
    assert resp.status_code == 200
    data = resp.json()
    assert "execution" in data
    assert "dependencies" in data
    assert "X-Request-ID" in resp.headers


def test_missing_route_returns_request_id(api_client):
    resp = api_client.get("/nonexistent-route-that-404s")
    assert resp.status_code == 404
    assert "X-Request-ID" in resp.headers


def test_health_response_has_execution_engine_status(api_client):
    resp = api_client.get("/monitoring")
    assert resp.status_code == 200
    exec_data = resp.json().get("execution", {})
    assert "status" in exec_data


def test_health_response_has_dependencies(api_client):
    resp = api_client.get("/health/details")
    assert resp.status_code == 200
    deps = resp.json().get("dependencies", {})
    assert isinstance(deps, dict)


def test_errors_is_null_when_no_failures(api_client):
    resp = api_client.get("/monitoring")
    assert resp.status_code == 200
    errs = resp.json().get("errors")
    assert errs is None


def test_db_tables_in_health_details(api_client):
    resp = api_client.get("/health/details")
    assert resp.status_code == 200
    tbl = resp.json().get("database_tables", {})
    assert "status" in tbl


# ─── Council ───────────────────────────────────────────────────────────────


def test_get_council_status_endpoint(api_client):
    resp = api_client.get("/council")
    assert resp.status_code == 200
    body = resp.json()
    assert "agents" in body
    assert "agent_count" in body


# ─── Whale Activity ────────────────────────────────────────────────────────


def test_get_whale_activity_endpoint(api_client):
    resp = api_client.get("/whale/activity")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)


def test_get_risk_mixed_quantities(api_client, db_session):
    from database import PaperTrade, Trade
    # Clear previous trades
    db_session.query(Trade).delete()
    db_session.query(PaperTrade).delete()
    db_session.flush()

    # 1. Open trade with quantity = 2.0 (exposure = 50000.0 * 2.0 = 100000.0)
    t1 = Trade(
        symbol="BTCUSDT", side="LONG", entry=50000.0, stop=49250.0,
        tp1=51000.0, tp2=52000.0, rr=2.0, status="OPEN", pnl=0.0
    )
    db_session.add(t1)
    db_session.flush()
    pt1 = PaperTrade(
        position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=2.0, status="OPEN", pnl=0.0
    )
    db_session.add(pt1)

    # 2. Open trade with NO matching PaperTrade record (fallback qty = 1.0, exposure = 3000.0 * 1.0 = 3000.0)
    t2 = Trade(
        symbol="ETHUSDT", side="LONG", entry=3000.0, stop=2900.0,
        tp1=3200.0, tp2=3300.0, rr=2.0, status="OPEN", pnl=0.0
    )
    db_session.add(t2)
    db_session.flush()

    headers = {"Authorization": f"Bearer {_token_for_user(_make_user(db_session))}"}
    resp = api_client.get("/risk", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["open_trades"] == 2
    # Portfolio exposure should be 100000.0 + 3000.0 = 103000.0
    assert body["portfolio_exposure"] == 103000.0
    assert body["symbol_exposure"]["BTCUSDT"] == 100000.0
    assert body["symbol_exposure"]["ETHUSDT"] == 3000.0


def test_get_intelligence_mixed_quantities(api_client, db_session):
    from database import PaperTrade, Trade
    # Clear previous trades
    db_session.query(Trade).delete()
    db_session.query(PaperTrade).delete()
    db_session.flush()

    # 1. Closed trade with quantity = 3.0 (real dollar pnl = 100.0 * 3.0 = 300.0)
    t1 = Trade(
        symbol="BTCUSDT", side="LONG", entry=50000.0, stop=49250.0,
        tp1=51000.0, tp2=52000.0, rr=2.0, status="TP_HIT", pnl=100.0
    )
    db_session.add(t1)
    db_session.flush()
    pt1 = PaperTrade(
        position_id=t1.id, symbol="BTCUSDT", side="LONG",
        entry=50000.0, quantity=3.0, status="CLOSED", pnl=300.0
    )
    db_session.add(pt1)

    # 2. Closed trade with NO matching PaperTrade record (fallback qty = 1.0, real dollar pnl = -50.0 * 1.0 = -50.0)
    t2 = Trade(
        symbol="ETHUSDT", side="LONG", entry=3000.0, stop=2900.0,
        tp1=3200.0, tp2=3300.0, rr=2.0, status="SL_HIT", pnl=-50.0
    )
    db_session.add(t2)
    db_session.flush()

    resp = api_client.get("/intelligence")
    assert resp.status_code == 200
    body = resp.json()
    # Total PnL should be 300.0 - 50.0 = 250.0
    assert body["trades"]["total_pnl"] == 250.0
