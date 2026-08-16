"""Tests for api.main._broadcast_risk()'s per-user scoping.

Previously this summed EVERY tenant's open trades into one aggregate
number broadcast to every connected client -- any user could infer how
many positions other users collectively had open. Now it groups Trade
rows by owner and sends each owner only their own open_trades count via
WebSocketManager.broadcast_to_owner(), matching the per-user websocket
scoping added in api/websocket/manager.py.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

import api.main as main_module
from api.websocket.manager import WebSocketManager
from database import Trade


@pytest.fixture
def mock_manager(monkeypatch):
    manager = MagicMock(spec=WebSocketManager)
    manager.broadcast_to_owner = AsyncMock()
    manager.connected_user_ids = MagicMock(return_value=set())
    monkeypatch.setattr(main_module, "manager", manager)
    return manager


@pytest.fixture(autouse=True)
def patch_get_session(monkeypatch, session_factory):
    monkeypatch.setattr(main_module, "get_session", session_factory)


class TestBroadcastRiskPerUser:
    async def test_each_owner_gets_only_their_own_open_trades_count(self, db_session, mock_manager):
        db_session.add_all([
            Trade(symbol="BTCUSDT", side="LONG", entry=50000.0, status="OPEN", user_id=1),
            Trade(symbol="ETHUSDT", side="LONG", entry=3000.0, status="OPEN", user_id=1),
            Trade(symbol="SOLUSDT", side="SHORT", entry=100.0, status="OPEN", user_id=2),
            Trade(symbol="ADAUSDT", side="LONG", entry=1.0, status="CLOSED", user_id=2),
        ])
        db_session.commit()

        await main_module._broadcast_risk()

        calls = {
            c.args[1]: json.loads(c.args[0])["payload"]["open_trades"]
            for c in mock_manager.broadcast_to_owner.await_args_list
        }
        assert calls == {1: 2, 2: 1}

    async def test_orphaned_trades_go_to_none_owner(self, db_session, mock_manager):
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", entry=50000.0, status="OPEN", user_id=None))
        db_session.commit()

        await main_module._broadcast_risk()

        calls = {
            c.args[1]: json.loads(c.args[0])["payload"]["open_trades"]
            for c in mock_manager.broadcast_to_owner.await_args_list
        }
        assert calls == {None: 1}

    async def test_connected_user_with_zero_trades_still_gets_an_update(self, db_session, mock_manager):
        mock_manager.connected_user_ids = MagicMock(return_value={7})

        await main_module._broadcast_risk()

        calls = {
            c.args[1]: json.loads(c.args[0])["payload"]["open_trades"]
            for c in mock_manager.broadcast_to_owner.await_args_list
        }
        assert calls == {7: 0}
