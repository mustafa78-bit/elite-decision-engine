import logging
import time
import uuid
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from api.websocket import WSManager, WSEvent, WSEventType, WSConnectionInfo, validate_topic

logger = logging.getLogger(__name__)


class Channel(str, Enum):
    DASHBOARD = "dashboard"
    PORTFOLIO = "portfolio"
    INTELLIGENCE = "intelligence"
    NOTIFICATIONS = "notifications"
    DECISIONS = "decisions"
    HEALTH = "health"
    METRICS = "metrics"
    TRADES = "trades"


_VALID_CHANNELS = frozenset(c.value for c in Channel)


def validate_channel(channel: str) -> bool:
    return channel in _VALID_CHANNELS


@dataclass
class Subscription:
    connection_id: str
    channels: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "channels": list(self.channels),
            "created_at": self.created_at,
        }


class ChannelRegistry:
    def __init__(self):
        self._channels: Dict[str, Set[str]] = {c.value: set() for c in Channel}

    def subscribe(self, connection_id: str, channel: str) -> bool:
        if channel not in self._channels:
            return False
        self._channels[channel].add(connection_id)
        return True

    def unsubscribe(self, connection_id: str, channel: str) -> None:
        if channel in self._channels:
            self._channels[channel].discard(connection_id)

    def unsubscribe_all(self, connection_id: str) -> None:
        for channel in self._channels:
            self._channels[channel].discard(connection_id)

    def get_subscribers(self, channel: str) -> Set[str]:
        return set(self._channels.get(channel, set()))

    def get_all_channels(self) -> Dict[str, int]:
        return {ch: len(sub) for ch, sub in self._channels.items()}

    def has_subscribers(self, channel: str) -> bool:
        return len(self._channels.get(channel, set())) > 0


class SubscriptionManager:
    def __init__(self):
        self._subscriptions: Dict[str, Subscription] = {}

    def register(self, connection_id: str) -> Subscription:
        if connection_id not in self._subscriptions:
            self._subscriptions[connection_id] = Subscription(connection_id=connection_id)
        return self._subscriptions[connection_id]

    def unregister(self, connection_id: str) -> None:
        self._subscriptions.pop(connection_id, None)

    def get_subscription(self, connection_id: str) -> Optional[Subscription]:
        return self._subscriptions.get(connection_id)

    def active_count(self) -> int:
        return len(self._subscriptions)

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "active_subscriptions": self.active_count(),
            "connection_ids": list(self._subscriptions.keys()),
        }


class EventThrottle:
    def __init__(self, min_interval: float = 1.0):
        self._min_interval = min_interval
        self._last_sent: Dict[str, float] = {}
        self._total_throttled = 0

    def can_send(self, event_type: str) -> bool:
        now = time.time()
        last = self._last_sent.get(event_type, 0.0)
        if now - last >= self._min_interval:
            self._last_sent[event_type] = now
            return True
        self._total_throttled += 1
        return False

    def reset(self, event_type: Optional[str] = None) -> None:
        if event_type:
            self._last_sent.pop(event_type, None)
        else:
            self._last_sent.clear()

    @property
    def throttled_count(self) -> int:
        return self._total_throttled

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "min_interval": self._min_interval,
            "total_throttled": self._total_throttled,
            "tracked_types": list(self._last_sent.keys()),
        }


@dataclass
class EventBatch:
    events: List[WSEvent] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    channel: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "events": [e.to_dict() for e in self.events],
            "created_at": self.created_at,
            "channel": self.channel,
            "count": len(self.events),
        }


class EventBatcher:
    def __init__(self, max_batch_size: int = 10, max_wait: float = 0.5):
        self._max_batch_size = max_batch_size
        self._max_wait = max_wait
        self._batches: Dict[str, EventBatch] = {}
        self._total_batches_created = 0
        self._total_events_batched = 0

    def add(self, channel: str, event: WSEvent) -> Optional[List[WSEvent]]:
        if channel not in self._batches:
            self._batches[channel] = EventBatch(channel=channel)
            self._total_batches_created += 1
        self._batches[channel].events.append(event)
        self._total_events_batched += 1
        if len(self._batches[channel].events) >= self._max_batch_size:
            return self.flush(channel)
        return None

    def flush(self, channel: Optional[str] = None) -> Optional[List[WSEvent]]:
        if channel:
            batch = self._batches.pop(channel, None)
            return batch.events if batch else None
        result = []
        for ch in list(self._batches.keys()):
            batch = self._batches.pop(ch, None)
            if batch:
                result.extend(batch.events)
        return result if result else None

    def ready_batches(self) -> Dict[str, List[WSEvent]]:
        now = time.time()
        ready: Dict[str, List[WSEvent]] = {}
        for channel, batch in list(self._batches.items()):
            if now - batch.created_at >= self._max_wait:
                ready[channel] = self._batches.pop(channel).events
        return ready

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "max_batch_size": self._max_batch_size,
            "max_wait": self._max_wait,
            "active_batches": len(self._batches),
            "total_batches_created": self._total_batches_created,
            "total_events_batched": self._total_events_batched,
        }


class HeartbeatGenerator:
    def __init__(self, interval: float = 30.0):
        self._interval = interval
        self._last_heartbeat: float = 0.0
        self._total_generated = 0

    def should_heartbeat(self) -> bool:
        now = time.time()
        if now - self._last_heartbeat >= self._interval:
            self._last_heartbeat = now
            return True
        return False

    def generate(self) -> WSEvent:
        self._total_generated += 1
        return WSEvent(
            event_type=WSEventType.HEARTBEAT,
            data={"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()},
            event_id=uuid.uuid4().hex[:12],
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "interval": self._interval,
            "total_generated": self._total_generated,
        }


class UnifiedBroadcaster:
    def __init__(self, ws_manager: WSManager):
        self._ws = ws_manager
        self._channel_registry = ChannelRegistry()
        self._subscription_manager = SubscriptionManager()
        self._throttle = EventThrottle(min_interval=0.5)
        self._batcher = EventBatcher(max_batch_size=10, max_wait=0.5)
        self._heartbeat = HeartbeatGenerator(interval=30.0)
        self._connection_cleanup_handler = self._on_connection_cleanup
        self._ws.on_cleanup(self._connection_cleanup_handler)
        self._diagnostics: Dict[str, Any] = {
            "broadcasts": 0,
            "throttled": 0,
            "batched": 0,
            "errors": 0,
        }

    def _on_connection_cleanup(self, connection_id: str) -> None:
        self._channel_registry.unsubscribe_all(connection_id)
        self._subscription_manager.unregister(connection_id)
        logger.debug("Cleaned up subscription for %s", connection_id)

    async def broadcast(self, channel: str, event: WSEvent) -> None:
        if not validate_channel(channel):
            logger.warning("Invalid channel: %s", channel)
            self._diagnostics["errors"] += 1
            return
        if not self._channel_registry.has_subscribers(channel):
            return
        if not self._throttle.can_send(event.event_type.value):
            self._diagnostics["throttled"] += 1
            return
        batched = self._batcher.add(channel, event)
        if batched:
            self._diagnostics["batched"] += len(batched)
            for ev in batched:
                self._diagnostics["broadcasts"] += 1
                await self._ws.broadcast(ev)
                logger.debug("Broadcast %s on %s", ev.event_id[:8], channel)
        ready = self._batcher.ready_batches()
        for ch, events in ready.items():
            for ev in events:
                self._diagnostics["broadcasts"] += 1
                await self._ws.broadcast(ev)

    async def broadcast_immediate(self, channel: str, event: WSEvent) -> None:
        if not validate_channel(channel):
            logger.warning("Invalid channel: %s", channel)
            return
        self._diagnostics["broadcasts"] += 1
        await self._ws.broadcast(event)

    async def flush_all(self) -> None:
        batches = self._batcher.flush()
        if batches:
            for ev in batches:
                self._diagnostics["broadcasts"] += 1
                await self._ws.broadcast(ev)

    async def maybe_heartbeat(self) -> None:
        if self._heartbeat.should_heartbeat():
            event = self._heartbeat.generate()
            await self._ws.broadcast(event)

    def subscribe(self, connection_id: str, channel: str) -> bool:
        if not validate_channel(channel):
            return False
        sub = self._subscription_manager.register(connection_id)
        sub.channels.add(channel)
        ok = self._channel_registry.subscribe(connection_id, channel)
        return ok

    def unsubscribe(self, connection_id: str, channel: str) -> None:
        if not validate_channel(channel):
            return
        sub = self._subscription_manager.get_subscription(connection_id)
        if sub:
            sub.channels.discard(channel)
        self._channel_registry.unsubscribe(connection_id, channel)

    def unsubscribe_all(self, connection_id: str) -> None:
        self._channel_registry.unsubscribe_all(connection_id)
        self._subscription_manager.unregister(connection_id)

    def get_broadcast_metrics(self) -> Dict[str, Any]:
        return {
            **self._diagnostics,
            "throttle": self._throttle.get_diagnostics(),
            "batcher": self._batcher.get_diagnostics(),
            "heartbeat": self._heartbeat.get_diagnostics(),
        }

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            **self._diagnostics,
            "active_connections": self._subscription_manager.active_count(),
            "channels": self._channel_registry.get_all_channels(),
            "throttle": self._throttle.get_diagnostics(),
            "batcher": self._batcher.get_diagnostics(),
        }


class DashboardRefreshScheduler:
    def __init__(self, interval: float = 60.0):
        self._interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._shutdown = threading.Event()
        self._callbacks: List[Callable] = []
        self._refresh_count = 0
        self._errors = 0

    def add_callback(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._shutdown.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="dashboard-refresh")
        self._thread.start()
        logger.info("Dashboard refresh scheduler started (interval=%s)", self._interval)

    def stop(self) -> None:
        self._shutdown.set()
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("Dashboard refresh scheduler stopped")

    def _run(self) -> None:
        while not self._shutdown.is_set():
            for cb in self._callbacks:
                if self._shutdown.is_set():
                    break
                try:
                    cb()
                    self._refresh_count += 1
                except Exception:
                    self._errors += 1
                    logger.exception("Dashboard refresh callback failed")
            self._shutdown.wait(timeout=self._interval)

    @property
    def is_running(self) -> bool:
        return self._running

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "interval": self._interval,
            "refresh_count": self._refresh_count,
            "callbacks": len(self._callbacks),
            "errors": self._errors,
        }
