from fastapi.testclient import TestClient

from api.main import app, manager
from api.websocket.manager import WebSocketManager


def test_app_is_fastapi_instance():
    assert app.title == "Elite Decision Engine"


def test_manager_is_websocket_manager():
    assert isinstance(manager, WebSocketManager)


def test_websocket_connect_and_disconnect():
    from auth.jwt import create_access_token
    token = create_access_token({"sub": "1", "username": "test"})
    client = TestClient(app)
    with client.websocket_connect(f"/ws/trades?token={token}") as ws:
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
    expected = {"/performance", "/portfolio", "/risk", "/position-sizing", "/signals", "/health", "/market"}
    for p in expected:
        assert p in paths, f"Missing route: {p}"


def test_cors_preflight_on_protected_route_gets_cors_headers_not_bare_401():
    """CORSMiddleware must run before auth_middleware so a preflight OPTIONS
    request to a protected route gets real CORS headers back, instead of a
    header-less 401 from auth_middleware that the browser would treat as a
    failed preflight and block the real request entirely. Regression test for
    the middleware-ordering bug described in docs/FRONTEND_AUTH_FIX_REPORT.md.
    """
    client = TestClient(app)
    resp = client.options(
        "/portfolio",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
