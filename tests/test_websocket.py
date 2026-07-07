from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.routes.ws import router as ws_router
from api.websocket.manager import ConnectionManager


@pytest.fixture
def app() -> FastAPI:
    _app = FastAPI()
    _app.state.ws_manager = ConnectionManager()
    _app.include_router(ws_router)
    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestConnectionManager:
    @staticmethod
    def _mock_ws() -> MagicMock:
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    def test_connect_adds_client(self) -> None:
        mgr = ConnectionManager()
        ws = self._mock_ws()

        async def run() -> None:
            await mgr.connect(ws, "alice")
            assert mgr.active_count == 1
            assert "alice" in mgr.active_clients

        asyncio.run(run())

    def test_disconnect_removes_client(self) -> None:
        mgr = ConnectionManager()
        ws = self._mock_ws()

        async def run() -> None:
            await mgr.connect(ws, "alice")
            mgr.disconnect("alice")
            assert mgr.active_count == 0

        asyncio.run(run())

    def test_disconnect_unknown_does_not_raise(self) -> None:
        mgr = ConnectionManager()
        mgr.disconnect("nonexistent")
        assert mgr.active_count == 0

    def test_broadcast_sends_to_all(self) -> None:
        mgr = ConnectionManager()
        ws1 = self._mock_ws()
        ws2 = self._mock_ws()
        event = {"type": "HEALTH", "status": "HEALTHY"}

        async def run() -> None:
            await mgr.connect(ws1, "c1")
            await mgr.connect(ws2, "c2")
            await mgr.broadcast(event)
            ws1.send_json.assert_called_once_with(event)
            ws2.send_json.assert_called_once_with(event)

        asyncio.run(run())

    def test_broadcast_removes_failed_client(self) -> None:
        mgr = ConnectionManager()
        ws1 = self._mock_ws()
        ws2 = self._mock_ws()
        ws2.send_json = AsyncMock(side_effect=Exception("gone"))

        async def run() -> None:
            await mgr.connect(ws1, "c1")
            await mgr.connect(ws2, "c2")
            await mgr.broadcast({"type": "TEST"})
            assert mgr.active_count == 1
            assert mgr.active_clients == ["c1"]

        asyncio.run(run())

    def test_send_to_existing_client(self) -> None:
        mgr = ConnectionManager()
        ws = self._mock_ws()

        async def run() -> None:
            await mgr.connect(ws, "c1")
            ok = await mgr.send_to("c1", {"type": "PING"})
            assert ok is True
            ws.send_json.assert_called_once()

        asyncio.run(run())

    def test_send_to_unknown_client_returns_false(self) -> None:
        mgr = ConnectionManager()

        async def run() -> None:
            ok = await mgr.send_to("ghost", {"type": "PING"})
            assert ok is False

        asyncio.run(run())

    def test_send_to_failed_client_removes_it(self) -> None:
        mgr = ConnectionManager()
        ws = self._mock_ws()
        ws.send_json = AsyncMock(side_effect=Exception("gone"))

        async def run() -> None:
            await mgr.connect(ws, "c1")
            ok = await mgr.send_to("c1", {"type": "PING"})
            assert ok is False
            assert mgr.active_count == 0

        asyncio.run(run())

    def test_active_count_multiple_clients(self) -> None:
        mgr = ConnectionManager()

        async def run() -> None:
            for i in range(5):
                ws = self._mock_ws()
                await mgr.connect(ws, str(i))
            assert mgr.active_count == 5

        asyncio.run(run())


class TestWebSocketEndpoint:
    def test_connect(self, client: TestClient) -> None:
        with client.websocket_connect("/ws") as ws:
            assert ws is not None

    def test_client_registered_on_connect(self, client: TestClient, app: FastAPI) -> None:
        assert app.state.ws_manager.active_count == 0
        with client.websocket_connect("/ws"):
            assert app.state.ws_manager.active_count == 1
        assert app.state.ws_manager.active_count == 0

    def test_multiple_clients(self, client: TestClient, app: FastAPI) -> None:
        with client.websocket_connect("/ws") as ws1:
            assert app.state.ws_manager.active_count == 1
            with client.websocket_connect("/ws") as ws2:
                assert app.state.ws_manager.active_count == 2
            assert app.state.ws_manager.active_count == 1
        assert app.state.ws_manager.active_count == 0

    def test_disconnect_removes_client(self, client: TestClient, app: FastAPI) -> None:
        with client.websocket_connect("/ws") as ws:
            assert app.state.ws_manager.active_count == 1
            ws.close()
        assert app.state.ws_manager.active_count == 0

    def test_invalid_json_does_not_disconnect(self, client: TestClient, app: FastAPI) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text("not valid json")
            ws.send_text("{}")
        assert app.state.ws_manager.active_count == 0

    def test_broadcast_via_manager(self, client: TestClient, app: FastAPI) -> None:
        mgr = app.state.ws_manager
        event = {"type": "TRADE", "symbol": "BTCUSDT", "side": "LONG", "status": "OPEN"}

        with client.websocket_connect("/ws") as ws1:
            with client.websocket_connect("/ws") as ws2:
                async def do_broadcast() -> None:
                    await mgr.broadcast(event)

                asyncio.run(do_broadcast())
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

        assert data1 == event
        assert data2 == event
