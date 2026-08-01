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


# ─── Backtest ──────────────────────────────────────────────────────────────


def test_get_backtest_empty(api_client):
    resp = api_client.get("/backtest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["total_signals"] == 0
    assert body["trades"]["total"] == 0


def test_get_backtest_with_data(api_client, db_session):
    _make_signal(db_session, status="EXECUTED", approved=True, confidence=90.0)
    _make_signal(db_session, status="REJECTED", approved=False, confidence=30.0)
    _make_trade(db_session, signal_id=1, status="CLOSED", pnl=500.0)
    _make_trade(db_session, signal_id=2, status="CLOSED", pnl=-200.0)
    resp = api_client.get("/backtest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["total_signals"] == 2
    assert body["summary"]["approved_signals"] == 1
    assert body["trades"]["total"] == 2
    assert body["trades"]["closed"] == 2
    assert body["performance"]["total_pnl"] == 300.0
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
