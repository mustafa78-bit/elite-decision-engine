import pytest
from unittest.mock import AsyncMock, MagicMock

from api.websocket.manager import WebSocketManager


@pytest.fixture
def manager():
    return WebSocketManager()


from auth.jwt import create_access_token

_TEST_TOKEN = create_access_token({"sub": "1", "username": "test"})


def _make_ws():
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.send_text.__name__ = "send_text"
    ws.close = AsyncMock()
    ws.query_params = {"token": _TEST_TOKEN}
    return ws


@pytest.fixture
def mock_ws():
    return _make_ws()


@pytest.mark.asyncio
async def test_connect_adds_client(manager, mock_ws):
    await manager.connect(mock_ws)
    assert mock_ws in manager._clients
    mock_ws.accept.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_removes_client(manager, mock_ws):
    await manager.connect(mock_ws)
    await manager.disconnect(mock_ws)
    assert mock_ws not in manager._clients


@pytest.mark.asyncio
async def test_broadcast_sends_to_all(manager):
    ws1 = _make_ws()
    ws2 = _make_ws()

    await manager.connect(ws1)
    await manager.connect(ws2)
    await manager.broadcast("hello")

    ws1.send_text.assert_awaited_once_with("hello")
    ws2.send_text.assert_awaited_once_with("hello")


@pytest.mark.asyncio
async def test_broadcast_removes_stale_clients(manager):
    ws_ok = _make_ws()
    ws_bad = _make_ws()
    ws_bad.send_text.side_effect = Exception("gone")

    await manager.connect(ws_ok)
    await manager.connect(ws_bad)
    await manager.broadcast("test")

    assert ws_bad not in manager._clients
    assert ws_ok in manager._clients
