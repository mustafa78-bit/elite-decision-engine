from fastapi.testclient import TestClient

from api.main import app, manager
from api.websocket.manager import WebSocketManager


def test_app_is_fastapi_instance():
    assert app.title == "Elite Decision Engine"


def test_manager_is_websocket_manager():
    assert isinstance(manager, WebSocketManager)


def test_websocket_connect_and_disconnect():
    client = TestClient(app)
    with client.websocket_connect("/ws/trades") as ws:
        ws.send_text("ping")
    assert len(manager._clients) == 0


def test_performance_route_registered():
    paths = list(app.openapi()["paths"])
    assert "/performance" in paths


def test_portfolio_route_registered():
    paths = list(app.openapi()["paths"])
    assert "/portfolio" in paths


def test_risk_route_registered():
    paths = list(app.openapi()["paths"])
    assert "/risk" in paths


def test_position_sizing_route_registered():
    paths = list(app.openapi()["paths"])
    assert "/position-sizing" in paths


def test_signals_route_registered():
    paths = list(app.openapi()["paths"])
    assert "/signals" in paths


def test_market_route_registered():
    paths = list(app.openapi()["paths"])
    assert "/market" in paths


def test_health_returns_ok():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "elite-decision-engine"


def test_all_api_routes_registered():
    paths = list(app.openapi()["paths"])
    expected = {"/performance", "/portfolio", "/risk", "/position-sizing", "/signals", "/health"}
    for p in expected:
        assert p in paths, f"Missing route: {p}"
