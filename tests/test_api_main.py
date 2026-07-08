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
