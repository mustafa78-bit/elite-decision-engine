from unittest.mock import AsyncMock, MagicMock

import pytest

from api.websocket.manager import WebSocketManager
from auth.jwt import create_access_token

_TEST_TOKEN = create_access_token({"sub": "1", "username": "test"})


@pytest.fixture
def manager():
    return WebSocketManager()


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


@pytest.mark.asyncio
async def test_broadcast_survives_concurrent_connect_mid_iteration(manager):
    """A client connecting while broadcast() is mid-loop must not crash the
    broadcast (RuntimeError: Set changed size during iteration) -- regression
    test for iterating the live `_clients` set instead of a snapshot.
    """
    ws1 = _make_ws()
    ws2 = _make_ws()
    late_joiner = _make_ws()

    async def add_client_mid_send(*args, **kwargs):
        manager._clients.add(late_joiner)

    ws1.send_text.side_effect = add_client_mid_send

    await manager.connect(ws1)
    await manager.connect(ws2)

    await manager.broadcast("hello")

    ws1.send_text.assert_awaited_once_with("hello")
    ws2.send_text.assert_awaited_once_with("hello")
    assert late_joiner in manager._clients
