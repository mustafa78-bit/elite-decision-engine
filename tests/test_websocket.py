import time
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from api.websocket import (
    WSManager, WSEvent, WSEventType, WSConnectionInfo,
    EventHistory, validate_topic, check_topic_permission,
)


class TestWSManagerRegistration:

    @pytest.fixture
    def manager(self):
        return WSManager(max_connections=10)

    @pytest.mark.asyncio
    async def test_register(self, manager):
        conn = AsyncMock()
        cid = await manager.register(conn, "127.0.0.1")
        assert cid is not None
        assert manager.active_connections == 1
        info = manager.get_connection(cid)
        assert info is not None
        assert info.client_ip == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_unregister(self, manager):
        conn = AsyncMock()
        cid = await manager.register(conn)
        result = await manager.unregister(conn)
        assert result == cid
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_unregister_unknown(self, manager):
        conn = AsyncMock()
        result = await manager.unregister(conn)
        assert result is None

    @pytest.mark.asyncio
    async def test_register_max_connections_evicts_oldest(self, manager):
        conns = []
        for _ in range(12):
            c = AsyncMock()
            cid = await manager.register(c)
            conns.append((c, cid))
        assert manager.active_connections == 10

    @pytest.mark.asyncio
    async def test_register_reconnect(self, manager):
        old_conn = AsyncMock()
        old_cid = await manager.register(old_conn)
        new_conn = AsyncMock()
        new_cid = await manager.register_reconnect(old_cid, new_conn, "10.0.0.1")
        assert new_cid != old_cid
        info = manager.get_connection(new_cid)
        assert info is not None
        assert info.reconnect_count == 1
        assert manager.active_connections == 1

    @pytest.mark.asyncio
    async def test_register_reconnect_preserves_topics(self, manager):
        old_conn = AsyncMock()
        old_cid = await manager.register(old_conn)
        manager.subscribe(old_cid, "dashboard")
        new_conn = AsyncMock()
        new_cid = await manager.register_reconnect(old_cid, new_conn)
        info = manager.get_connection(new_cid)
        assert "dashboard" in info.topics


class TestWSManagerHeartbeat:

    @pytest.fixture
    def manager(self):
        return WSManager()

    @pytest.mark.asyncio
    async def test_mark_heartbeat(self, manager):
        conn = AsyncMock()
        cid = await manager.register(conn)
        assert manager.mark_heartbeat(cid) is True
        assert manager.mark_heartbeat("nonexistent") is False

    @pytest.mark.asyncio
    async def test_cleanup_stale(self, manager):
        conn = AsyncMock()
        cid = await manager.register(conn)
        info = manager.get_connection(cid)
        info.last_heartbeat = time.time() - 120
        cleaned = await manager.cleanup_stale()
        assert cleaned >= 1
        assert manager.active_connections == 0


class TestWSManagerBroadcast:

    @pytest.fixture
    def manager(self):
        return WSManager(max_connections=10)

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self, manager):
        conns = [AsyncMock() for _ in range(3)]
        for c in conns:
            await manager.register(c)
        event = WSEvent(event_type=WSEventType.HEALTH, data={"status": "ok"})
        await manager.broadcast(event)
        for c in conns:
            c.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_removes_stale(self, manager):
        conn1 = AsyncMock()
        conn2 = AsyncMock()
        conn2.send_json.side_effect = Exception("disconnected")
        await manager.register(conn1)
        await manager.register(conn2)
        event = WSEvent(event_type=WSEventType.HEALTH, data={})
        await manager.broadcast(event)
        assert manager.active_connections == 1

    @pytest.mark.asyncio
    async def test_send_to_specific(self, manager):
        conn1 = AsyncMock()
        conn2 = AsyncMock()
        cid1 = await manager.register(conn1)
        await manager.register(conn2)
        event = WSEvent(event_type=WSEventType.HEALTH, data={})
        ok = await manager.send_to(cid1, event)
        assert ok is True
        conn1.send_json.assert_called_once()
        conn2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_to_nonexistent(self, manager):
        event = WSEvent(event_type=WSEventType.HEALTH, data={})
        ok = await manager.send_to("fake", event)
        assert ok is False


class TestWSManagerSubscription:

    @pytest.fixture
    def manager(self):
        return WSManager()

    @pytest.mark.asyncio
    async def test_subscribe(self, manager):
        conn = AsyncMock()
        cid = await manager.register(conn)
        assert manager.subscribe(cid, "dashboard") is True
        info = manager.get_connection(cid)
        assert "dashboard" in info.topics

    @pytest.mark.asyncio
    async def test_subscribe_invalid_topic(self, manager):
        conn = AsyncMock()
        cid = await manager.register(conn)
        assert manager.subscribe(cid, "invalid_topic") is False

    @pytest.mark.asyncio
    async def test_unsubscribe(self, manager):
        conn = AsyncMock()
        cid = await manager.register(conn)
        manager.subscribe(cid, "dashboard")
        assert manager.unsubscribe(cid, "dashboard") is True
        info = manager.get_connection(cid)
        assert "dashboard" not in info.topics

    @pytest.mark.asyncio
    async def test_subscription_diagnostics(self, manager):
        conn1 = AsyncMock()
        conn2 = AsyncMock()
        cid1 = await manager.register(conn1)
        cid2 = await manager.register(conn2)
        manager.subscribe(cid1, "dashboard")
        manager.subscribe(cid1, "portfolio")
        manager.subscribe(cid2, "dashboard")
        diag = manager.get_subscription_diagnostics()
        assert diag["topics"]["dashboard"] == 2
        assert diag["topics"]["portfolio"] == 1
        assert diag["total_subscriptions"] == 3


class TestWSManagerMetrics:

    @pytest.fixture
    def manager(self):
        return WSManager()

    @pytest.mark.asyncio
    async def test_get_connection_stats_empty(self, manager):
        stats = manager.get_connection_stats()
        assert stats["total"] == 0

    @pytest.mark.asyncio
    async def test_get_connection_stats(self, manager):
        conn = AsyncMock()
        await manager.register(conn)
        stats = manager.get_connection_stats()
        assert stats["total"] == 1
        assert stats["min_uptime"] >= 0

    @pytest.mark.asyncio
    async def test_get_metrics(self, manager):
        conn = AsyncMock()
        await manager.register(conn)
        metrics = manager.get_metrics()
        assert "active_connections" in metrics
        assert "total_connections_ever" in metrics
        assert "event_history_size" in metrics
        assert "subscription_diagnostics" in metrics
        assert "connection_stats" in metrics
        assert metrics["active_connections"] == 1

    @pytest.mark.asyncio
    async def test_metrics_track_broadcasts(self, manager):
        conn = AsyncMock()
        await manager.register(conn)
        event = WSEvent(event_type=WSEventType.HEALTH, data={})
        await manager.broadcast(event)
        metrics = manager.get_metrics()
        assert metrics["total_broadcasts"] >= 1
        assert metrics["event_history_size"] >= 1


class TestWSManagerEventHistory:

    @pytest.fixture
    def manager(self):
        return WSManager()

    @pytest.mark.asyncio
    async def test_event_history_records_broadcasts(self, manager):
        conn = AsyncMock()
        await manager.register(conn)
        event = WSEvent(event_type=WSEventType.HEALTH, data={"status": "ok"})
        await manager.broadcast(event)
        history = manager.get_event_history(limit=10)
        assert len(history) >= 1
        assert history[0]["event_type"] == "health"

    @pytest.mark.asyncio
    async def test_event_history_filter(self, manager):
        conn = AsyncMock()
        await manager.register(conn)
        await manager.broadcast(WSEvent(event_type=WSEventType.HEALTH, data={}))
        await manager.broadcast(WSEvent(event_type=WSEventType.DECISION, data={}))
        health_events = manager.get_event_history(limit=10, event_type=WSEventType.HEALTH)
        assert len(health_events) == 1

    @pytest.mark.asyncio
    async def test_replay_events(self, manager):
        conn = AsyncMock()
        await manager.register(conn)
        await manager.broadcast(WSEvent(event_type=WSEventType.HEALTH, data={"i": 1}))
        await manager.broadcast(WSEvent(event_type=WSEventType.HEALTH, data={"i": 2}))
        replay = manager.get_replay_events(from_index=0)
        assert len(replay) == 2
        replay_later = manager.get_replay_events(from_index=1)
        assert len(replay_later) == 1


class TestWSConnectionInfo:

    def test_to_dict(self):
        conn = MagicMock()
        info = WSConnectionInfo(conn, "test123", "10.0.0.1")
        info.topics.add("dashboard")
        info.messages_sent = 5
        d = info.to_dict()
        assert d["connection_id"] == "test123"
        assert d["client_ip"] == "10.0.0.1"
        assert d["topics"] == ["dashboard"]
        assert d["messages_sent"] == 5
        assert d["reconnect_count"] == 0

    def test_is_timed_out(self):
        conn = MagicMock()
        info = WSConnectionInfo(conn, "test")
        info.last_heartbeat = time.time() - 120
        assert info.is_timed_out(timeout=60.0) is True

    def test_is_not_timed_out(self):
        conn = MagicMock()
        info = WSConnectionInfo(conn, "test")
        assert info.is_timed_out(timeout=60.0) is False

    def test_mark_heartbeat(self):
        conn = MagicMock()
        info = WSConnectionInfo(conn, "test")
        old = info.last_heartbeat
        info.mark_heartbeat()
        assert info.last_heartbeat >= old


class TestEventHistory:

    def test_record_and_get(self):
        h = EventHistory(max_events=10)
        assert h.size == 0
        h.record(WSEvent(event_type=WSEventType.HEALTH, data={}))
        assert h.size == 1
        events = h.get_recent(limit=10)
        assert len(events) == 1

    def test_max_events(self):
        h = EventHistory(max_events=5)
        for i in range(10):
            h.record(WSEvent(event_type=WSEventType.HEALTH, data={"i": i}))
        assert h.size == 5

    def test_filter_by_type(self):
        h = EventHistory()
        h.record(WSEvent(event_type=WSEventType.HEALTH, data={}))
        h.record(WSEvent(event_type=WSEventType.DECISION, data={}))
        health = h.get_recent(limit=10, event_type=WSEventType.HEALTH)
        assert len(health) == 1

    def test_replay(self):
        h = EventHistory()
        h.record(WSEvent(event_type=WSEventType.HEALTH, data={"i": 0}))
        h.record(WSEvent(event_type=WSEventType.HEALTH, data={"i": 1}))
        replay = h.replay(from_index=0)
        assert len(replay) == 2
        replay_from_1 = h.replay(from_index=1)
        assert len(replay_from_1) == 1

    def test_replay_out_of_range(self):
        h = EventHistory()
        assert h.replay(from_index=-1) == []
        assert h.replay(from_index=5) == []

    def test_clear(self):
        h = EventHistory()
        h.record(WSEvent(event_type=WSEventType.HEALTH, data={}))
        h.clear()
        assert h.size == 0


class TestValidation:

    def test_validate_topic(self):
        assert validate_topic("dashboard") is True
        assert validate_topic("portfolio") is True
        assert validate_topic("invalid") is False

    def test_check_topic_permission(self):
        assert check_topic_permission("dashboard", "read") is True
        assert check_topic_permission("dashboard", "write") is False
        assert check_topic_permission("admin", "admin") is True
        assert check_topic_permission("invalid", "read") is False
