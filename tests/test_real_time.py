import time
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from api.websocket import WSEvent, WSEventType, WSManager
from services.real_time import (
    ChannelRegistry, SubscriptionManager, EventThrottle, EventBatcher,
    HeartbeatGenerator, UnifiedBroadcaster, DashboardRefreshScheduler,
    Channel, validate_channel,
)


class TestValidateChannel:

    def test_valid(self):
        assert validate_channel("dashboard") is True
        assert validate_channel(Channel.PORTFOLIO.value) is True

    def test_invalid(self):
        assert validate_channel("invalid") is False


class TestChannelRegistry:

    def test_subscribe(self):
        reg = ChannelRegistry()
        assert reg.subscribe("conn1", Channel.DASHBOARD.value) is True
        assert reg.get_subscribers(Channel.DASHBOARD.value) == {"conn1"}

    def test_subscribe_invalid(self):
        reg = ChannelRegistry()
        assert reg.subscribe("conn1", "invalid") is False

    def test_unsubscribe(self):
        reg = ChannelRegistry()
        reg.subscribe("conn1", Channel.DASHBOARD.value)
        reg.unsubscribe("conn1", Channel.DASHBOARD.value)
        assert reg.get_subscribers(Channel.DASHBOARD.value) == set()

    def test_unsubscribe_all(self):
        reg = ChannelRegistry()
        reg.subscribe("conn1", Channel.DASHBOARD.value)
        reg.subscribe("conn1", Channel.PORTFOLIO.value)
        reg.unsubscribe_all("conn1")
        assert reg.get_subscribers(Channel.DASHBOARD.value) == set()
        assert reg.get_subscribers(Channel.PORTFOLIO.value) == set()

    def test_has_subscribers(self):
        reg = ChannelRegistry()
        assert reg.has_subscribers(Channel.DASHBOARD.value) is False
        reg.subscribe("conn1", Channel.DASHBOARD.value)
        assert reg.has_subscribers(Channel.DASHBOARD.value) is True

    def test_get_all_channels(self):
        reg = ChannelRegistry()
        reg.subscribe("conn1", Channel.DASHBOARD.value)
        channels = reg.get_all_channels()
        assert channels[Channel.DASHBOARD.value] == 1
        assert channels[Channel.PORTFOLIO.value] == 0


class TestSubscriptionManager:

    def test_register(self):
        mgr = SubscriptionManager()
        sub = mgr.register("conn1")
        assert sub.connection_id == "conn1"
        assert mgr.active_count() == 1

    def test_register_duplicate(self):
        mgr = SubscriptionManager()
        mgr.register("conn1")
        mgr.register("conn1")
        assert mgr.active_count() == 1

    def test_unregister(self):
        mgr = SubscriptionManager()
        mgr.register("conn1")
        mgr.unregister("conn1")
        assert mgr.active_count() == 0

    def test_get_subscription(self):
        mgr = SubscriptionManager()
        mgr.register("conn1")
        sub = mgr.get_subscription("conn1")
        assert sub is not None
        assert mgr.get_subscription("nonexistent") is None

    def test_get_diagnostics(self):
        mgr = SubscriptionManager()
        mgr.register("conn1")
        diag = mgr.get_diagnostics()
        assert diag["active_subscriptions"] == 1
        assert "connection_ids" in diag


class TestEventThrottle:

    def test_can_send_first(self):
        t = EventThrottle(min_interval=1.0)
        assert t.can_send("test") is True

    def test_can_send_throttled(self):
        t = EventThrottle(min_interval=10.0)
        assert t.can_send("test") is True
        assert t.can_send("test") is False
        assert t.throttled_count == 1

    def test_can_send_different_types(self):
        t = EventThrottle(min_interval=10.0)
        assert t.can_send("type_a") is True
        assert t.can_send("type_b") is True

    def test_reset(self):
        t = EventThrottle(min_interval=10.0)
        t.can_send("test")
        t.reset("test")
        assert t.can_send("test") is True

    def test_reset_all(self):
        t = EventThrottle(min_interval=10.0)
        t.can_send("a")
        t.can_send("b")
        t.reset()
        assert t.can_send("a") is True
        assert t.can_send("b") is True

    def test_get_diagnostics(self):
        t = EventThrottle(min_interval=2.0)
        t.can_send("x")
        diag = t.get_diagnostics()
        assert diag["min_interval"] == 2.0
        assert "total_throttled" in diag
        assert "tracked_types" in diag


class TestEventBatcher:

    def test_add_single(self):
        b = EventBatcher(max_batch_size=5, max_wait=10.0)
        event = WSEvent(event_type=WSEventType.HEALTH, data={"key": "val"})
        result = b.add("test_channel", event)
        assert result is None

    def test_add_triggers_flush(self):
        b = EventBatcher(max_batch_size=2, max_wait=10.0)
        e1 = WSEvent(event_type=WSEventType.HEALTH, data={"i": 1})
        e2 = WSEvent(event_type=WSEventType.HEALTH, data={"i": 2})
        b.add("ch", e1)
        result = b.add("ch", e2)
        assert result is not None
        assert len(result) == 2

    def test_flush_channel(self):
        b = EventBatcher(max_batch_size=5, max_wait=10.0)
        b.add("ch", WSEvent(event_type=WSEventType.HEALTH, data={}))
        flushed = b.flush("ch")
        assert flushed is not None
        assert len(flushed) == 1

    def test_flush_all(self):
        b = EventBatcher(max_batch_size=5, max_wait=10.0)
        b.add("ch1", WSEvent(event_type=WSEventType.HEALTH, data={}))
        b.add("ch2", WSEvent(event_type=WSEventType.HEALTH, data={}))
        all_events = b.flush()
        assert all_events is not None
        assert len(all_events) == 2

    def test_ready_batches(self):
        b = EventBatcher(max_batch_size=5, max_wait=-1.0)
        b.add("ch", WSEvent(event_type=WSEventType.HEALTH, data={}))
        ready = b.ready_batches()
        assert "ch" in ready

    def test_flush_empty(self):
        b = EventBatcher()
        assert b.flush() is None
        assert b.flush("nonexistent") is None

    def test_get_diagnostics(self):
        b = EventBatcher(max_batch_size=5, max_wait=1.0)
        b.add("ch", WSEvent(event_type=WSEventType.HEALTH, data={}))
        diag = b.get_diagnostics()
        assert diag["max_batch_size"] == 5
        assert diag["max_wait"] == 1.0
        assert diag["total_batches_created"] >= 1


class TestHeartbeatGenerator:

    def test_should_heartbeat_first(self):
        h = HeartbeatGenerator(interval=0.1)
        assert h.should_heartbeat() is True

    def test_should_not_heartbeat(self):
        h = HeartbeatGenerator(interval=60.0)
        h.should_heartbeat()
        assert h.should_heartbeat() is False

    def test_generate(self):
        h = HeartbeatGenerator()
        event = h.generate()
        assert event.event_type == WSEventType.HEARTBEAT
        assert "status" in event.data
        assert event.data["status"] == "alive"
        assert event.event_id != ""

    def test_get_diagnostics(self):
        h = HeartbeatGenerator(interval=15.0)
        diag = h.get_diagnostics()
        assert diag["interval"] == 15.0
        assert diag["total_generated"] == 0
        h.generate()
        diag = h.get_diagnostics()
        assert diag["total_generated"] == 1


class TestUnifiedBroadcaster:

    @pytest.fixture
    def mock_ws(self):
        ws = MagicMock(spec=WSManager)
        ws.active_connections = 0
        return ws

    @pytest.fixture
    def broadcaster(self, mock_ws):
        return UnifiedBroadcaster(ws_manager=mock_ws)

    def test_subscribe(self, broadcaster):
        assert broadcaster.subscribe("conn1", Channel.DASHBOARD.value) is True
        diag = broadcaster.get_diagnostics()
        assert diag["active_connections"] == 1
        assert diag["channels"][Channel.DASHBOARD.value] == 1

    def test_subscribe_invalid_channel(self, broadcaster):
        assert broadcaster.subscribe("conn1", "invalid") is False

    def test_unsubscribe(self, broadcaster):
        broadcaster.subscribe("conn1", Channel.DASHBOARD.value)
        broadcaster.unsubscribe("conn1", Channel.DASHBOARD.value)
        diag = broadcaster.get_diagnostics()
        assert diag["channels"][Channel.DASHBOARD.value] == 0

    def test_unsubscribe_invalid_channel(self, broadcaster):
        broadcaster.subscribe("conn1", Channel.DASHBOARD.value)
        broadcaster.unsubscribe("conn1", "invalid")
        diag = broadcaster.get_diagnostics()
        assert diag["channels"][Channel.DASHBOARD.value] == 1

    def test_unsubscribe_all(self, broadcaster):
        broadcaster.subscribe("conn1", Channel.DASHBOARD.value)
        broadcaster.subscribe("conn1", Channel.PORTFOLIO.value)
        broadcaster.unsubscribe_all("conn1")
        diag = broadcaster.get_diagnostics()
        assert diag["active_connections"] == 0
        assert diag["channels"][Channel.DASHBOARD.value] == 0

    def test_get_diagnostics(self, broadcaster):
        diag = broadcaster.get_diagnostics()
        assert "broadcasts" in diag
        assert "throttled" in diag
        assert "active_connections" in diag
        assert "channels" in diag
        assert "throttle" in diag
        assert "batcher" in diag

    def test_get_broadcast_metrics(self, broadcaster):
        metrics = broadcaster.get_broadcast_metrics()
        assert "broadcasts" in metrics
        assert "throttle" in metrics
        assert "batcher" in metrics
        assert "heartbeat" in metrics

    @pytest.mark.asyncio
    async def test_maybe_heartbeat(self, broadcaster):
        await broadcaster.maybe_heartbeat()

    @pytest.mark.asyncio
    async def test_broadcast_invalid_channel(self, broadcaster):
        event = WSEvent(event_type=WSEventType.HEALTH, data={})
        await broadcaster.broadcast("invalid", event)
        assert broadcaster.get_diagnostics()["errors"] == 1

    @pytest.mark.asyncio
    async def test_broadcast_no_subscribers(self, broadcaster):
        event = WSEvent(event_type=WSEventType.HEALTH, data={})
        await broadcaster.broadcast("dashboard", event)

    @pytest.mark.asyncio
    async def test_connection_cleanup_handler_registered(self, broadcaster):
        assert broadcaster._connection_cleanup_handler is not None


class TestDashboardRefreshScheduler:

    def test_start_stop(self):
        sched = DashboardRefreshScheduler(interval=0.1)
        assert sched.is_running is False
        sched.start()
        assert sched.is_running is True
        sched.stop()
        assert sched.is_running is False

    def test_get_diagnostics(self):
        sched = DashboardRefreshScheduler()
        diag = sched.get_diagnostics()
        assert "running" in diag
        assert "interval" in diag
        assert "refresh_count" in diag
        assert "callbacks" in diag
        assert "errors" in diag
        assert sched.is_running is False

    def test_add_callback(self):
        sched = DashboardRefreshScheduler()
        called = []
        def cb():
            called.append(True)
        sched.add_callback(cb)
        assert len(sched._callbacks) == 1

    def test_double_start(self):
        sched = DashboardRefreshScheduler(interval=0.1)
        sched.start()
        sched.start()
        assert sched.is_running is True
        sched.stop()

    def test_errors_tracked(self):
        sched = DashboardRefreshScheduler(interval=0.1)
        def failing():
            raise ValueError("fail")
        sched.add_callback(failing)
        diag_before = sched.get_diagnostics()
        assert diag_before["errors"] == 0
