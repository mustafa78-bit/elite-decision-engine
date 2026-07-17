import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class WSEventType(str, Enum):
    DECISION = "decision"
    SIGNAL = "signal"
    INTELLIGENCE = "intelligence"
    HEALTH = "health"
    METRICS = "metrics"
    TRADE = "trade"
    NOTIFICATION = "notification"
    DASHBOARD = "dashboard"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SUBSCRIPTION = "subscription"
    REPLAY = "replay"
    RECONNECT = "reconnect"


_TOPIC_PERMISSIONS: Dict[str, Set[str]] = {
    "dashboard": {"read"},
    "portfolio": {"read"},
    "intelligence": {"read"},
    "notifications": {"read", "write"},
    "decisions": {"read"},
    "health": {"read"},
    "metrics": {"read"},
    "trades": {"read"},
    "admin": {"read", "write", "admin"},
}


_VALID_TOPICS = frozenset(_TOPIC_PERMISSIONS.keys())


def validate_topic(topic: str) -> bool:
    return topic in _VALID_TOPICS


def check_topic_permission(topic: str, permission: str) -> bool:
    perms = _TOPIC_PERMISSIONS.get(topic, set())
    return permission in perms


@dataclass
class WSEvent:
    event_type: WSEventType
    data: Dict[str, Any]
    version: str = "2.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WSNotificationPayload:
    type: str = "info"
    title: str = ""
    message: str = ""
    severity: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WSDashboardPayload:
    portfolio: Dict[str, Any] = field(default_factory=dict)
    intelligence: Dict[str, Any] = field(default_factory=dict)
    risk: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WSSubscriptionPayload:
    topic: str = ""
    action: str = ""
    connection_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


MAX_EVENT_HISTORY = 500
_HEARTBEAT_TIMEOUT = 60.0
_STALE_CLEANUP_INTERVAL = 30.0


class WSConnectionInfo:
    __slots__ = ("conn", "connection_id", "connected_at", "last_heartbeat",
                 "topics", "messages_sent", "messages_received", "reconnect_count",
                 "is_stale", "client_ip")

    def __init__(self, conn, connection_id: str, client_ip: str = ""):
        self.conn = conn
        self.connection_id = connection_id
        self.connected_at = time.time()
        self.last_heartbeat = time.time()
        self.topics: Set[str] = set()
        self.messages_sent = 0
        self.messages_received = 0
        self.reconnect_count = 0
        self.is_stale = False
        self.client_ip = client_ip

    @property
    def uptime(self) -> float:
        return time.time() - self.connected_at

    def mark_heartbeat(self) -> None:
        self.last_heartbeat = time.time()

    def is_timed_out(self, timeout: float = _HEARTBEAT_TIMEOUT) -> bool:
        return time.time() - self.last_heartbeat > timeout

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "connected_at": datetime.fromtimestamp(self.connected_at, tz=timezone.utc).isoformat(),
            "uptime": round(self.uptime, 2),
            "last_heartbeat": datetime.fromtimestamp(self.last_heartbeat, tz=timezone.utc).isoformat(),
            "topics": list(self.topics),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "reconnect_count": self.reconnect_count,
            "is_stale": self.is_stale,
            "client_ip": self.client_ip,
        }


class EventHistory:
    def __init__(self, max_events: int = MAX_EVENT_HISTORY):
        self._events: List[WSEvent] = []
        self._max_events = max_events

    def record(self, event: WSEvent) -> None:
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    def get_recent(self, limit: int = 50, event_type: Optional[WSEventType] = None) -> List[Dict[str, Any]]:
        filtered = self._events
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        return [e.to_dict() for e in filtered[-limit:]]

    def replay(self, from_index: int = 0) -> List[WSEvent]:
        if from_index < 0 or from_index >= len(self._events):
            return []
        return list(self._events[from_index:])

    @property
    def size(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()


class WSManager:
    def __init__(self, max_connections: int = 1000):
        self._connections: Dict[str, WSConnectionInfo] = {}
        self._max_connections = max_connections
        self._event_history = EventHistory()
        self._metrics: Dict[str, Any] = {
            "total_connections_ever": 0,
            "total_disconnections": 0,
            "total_broadcasts": 0,
            "total_events_recorded": 0,
            "broadcast_errors": 0,
            "total_throttled": 0,
            "stale_connections_removed": 0,
            "reconnect_events": 0,
        }
        self._cleanup_handlers: List[Callable] = []

    def on_cleanup(self, handler: Callable) -> None:
        self._cleanup_handlers.append(handler)

    def _generate_id(self) -> str:
        return uuid.uuid4().hex[:12]

    async def register(self, connection, client_ip: str = "") -> str:
        connection_id = self._generate_id()
        info = WSConnectionInfo(connection, connection_id, client_ip)
        self._connections[connection_id] = info
        self._metrics["total_connections_ever"] += 1
        if len(self._connections) > self._max_connections:
            oldest = min(self._connections.values(), key=lambda c: c.connected_at)
            await self.unregister(oldest.conn)
        logger.info("WS connection registered: %s", connection_id)
        return connection_id

    async def unregister(self, connection) -> Optional[str]:
        connection_id = None
        for cid, info in list(self._connections.items()):
            if info.conn is connection:
                connection_id = cid
                del self._connections[cid]
                self._metrics["total_disconnections"] += 1
                for handler in self._cleanup_handlers:
                    try:
                        handler(cid)
                    except Exception:
                        logger.exception("Cleanup handler failed for %s", cid)
                logger.info("WS connection unregistered: %s", cid)
                break
        return connection_id

    async def register_reconnect(self, old_connection_id: str, new_connection, client_ip: str = "") -> Optional[str]:
        old_info = self._connections.pop(old_connection_id, None)
        new_id = self._generate_id()
        info = WSConnectionInfo(new_connection, new_id, client_ip)
        if old_info:
            info.reconnect_count = old_info.reconnect_count + 1
            info.topics = old_info.topics
        self._connections[new_id] = info
        self._metrics["reconnect_events"] += 1
        logger.info("WS reconnection: %s -> %s", old_connection_id, new_id)
        return new_id

    async def broadcast(self, event: WSEvent) -> None:
        payload = event.to_dict()
        self._event_history.record(event)
        self._metrics["total_events_recorded"] += 1
        stale: List[str] = []
        for cid, info in self._connections.items():
            try:
                await info.conn.send_json(payload)
                info.messages_sent += 1
            except Exception:
                logger.debug("Broadcast failed to %s, marking stale", cid)
                stale.append(cid)
        for cid in stale:
            await self._remove_stale(cid)
        self._metrics["total_broadcasts"] += 1

    async def send_to(self, connection_id: str, event: WSEvent) -> bool:
        info = self._connections.get(connection_id)
        if info is None:
            return False
        try:
            payload = event.to_dict()
            await info.conn.send_json(payload)
            info.messages_sent += 1
            return True
        except Exception:
            logger.debug("Send to %s failed", connection_id)
            await self._remove_stale(connection_id)
            return False

    async def _remove_stale(self, connection_id: str) -> None:
        info = self._connections.pop(connection_id, None)
        if info:
            self._metrics["stale_connections_removed"] += 1
            info.is_stale = True
            for handler in self._cleanup_handlers:
                try:
                    handler(connection_id)
                except Exception:
                    pass

    async def cleanup_stale(self) -> int:
        now = time.time()
        stale_ids = [
            cid for cid, info in self._connections.items()
            if now - info.last_heartbeat > _HEARTBEAT_TIMEOUT
        ]
        for cid in stale_ids:
            await self._remove_stale(cid)
        if stale_ids:
            logger.info("Cleaned %d stale connections", len(stale_ids))
        return len(stale_ids)

    def mark_heartbeat(self, connection_id: str) -> bool:
        info = self._connections.get(connection_id)
        if info:
            info.mark_heartbeat()
            return True
        return False

    def subscribe(self, connection_id: str, topic: str) -> bool:
        info = self._connections.get(connection_id)
        if not info or not validate_topic(topic):
            return False
        info.topics.add(topic)
        return True

    def unsubscribe(self, connection_id: str, topic: str) -> bool:
        info = self._connections.get(connection_id)
        if not info:
            return False
        info.topics.discard(topic)
        return True

    def get_connection(self, connection_id: str) -> Optional[WSConnectionInfo]:
        return self._connections.get(connection_id)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    def get_event_history(self, limit: int = 50, event_type: Optional[WSEventType] = None) -> List[Dict[str, Any]]:
        return self._event_history.get_recent(limit=limit, event_type=event_type)

    def get_replay_events(self, from_index: int = 0) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._event_history.replay(from_index=from_index)]

    def get_connection_info(self) -> Dict[str, Any]:
        return {
            "active_connections": len(self._connections),
            "max_connections": self._max_connections,
            "connections": [info.to_dict() for info in self._connections.values()],
        }

    def get_connection_stats(self) -> Dict[str, Any]:
        if not self._connections:
            return {"min_uptime": 0, "max_uptime": 0, "avg_uptime": 0, "total": 0}
        uptimes = [c.uptime for c in self._connections.values()]
        return {
            "total": len(self._connections),
            "min_uptime": round(min(uptimes), 2),
            "max_uptime": round(max(uptimes), 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 2),
        }

    def get_subscription_diagnostics(self) -> Dict[str, Any]:
        topic_counts: Dict[str, int] = defaultdict(int)
        for info in self._connections.values():
            for topic in info.topics:
                topic_counts[topic] += 1
        return {
            "topics": dict(topic_counts),
            "total_subscriptions": sum(topic_counts.values()),
            "unique_topics": list(topic_counts.keys()),
        }

    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self._metrics,
            "active_connections": self.active_connections,
            "event_history_size": self._event_history.size,
            "subscription_diagnostics": self.get_subscription_diagnostics(),
            "connection_stats": self.get_connection_stats(),
        }
