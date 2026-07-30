import logging
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class BlackboardEvent:
    """
    NEXUS Versioned Blackboard Event.
    Captures complete context, event metadata, parentage tracing, versioning,
    producer metadata, and timestamps for robust observability and replay.
    """
    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        producer: str,
        priority: EventPriority = EventPriority.MEDIUM,
        parent_id: Optional[str] = None,
        version: str = "1.0.0"
    ):
        self.event_id: str = str(uuid.uuid4())
        self.parent_id: Optional[str] = parent_id
        self.event_type: str = event_type
        self.payload: Dict[str, Any] = payload
        self.producer: str = producer
        self.priority: EventPriority = priority
        self.version: str = version
        self.timestamp: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "parent_id": self.parent_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "producer": self.producer,
            "priority": self.priority.name,
            "version": self.version,
            "timestamp": self.timestamp.isoformat()
        }

class CognitiveBlackboard:
    """
    NEXUS Cognitive Blackboard Space.
    Orchestrates the common working area for asynchronous and synchronous cognitive agents
    by implementing structured priorities, conflict resolution, observability logs, and audit replays.
    """
    def __init__(self):
        self.events_by_id: Dict[str, BlackboardEvent] = {}
        self.queue: List[BlackboardEvent] = []
        self.subscribers: Dict[str, List[Any]] = {}
        self.replay_buffer: List[Dict[str, Any]] = []

    def register_subscriber(self, event_type: str, handler: Any) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def post_event(self, event: BlackboardEvent) -> None:
        self.events_by_id[event.event_id] = event
        self.queue.append(event)
        # Sort queue by Priority (lower Enum value is higher priority)
        self.queue.sort(key=lambda ev: ev.priority.value)

        # Log to replay buffer for observability
        self.replay_buffer.append(event.to_dict())
        logger.debug(f"Posted Event [{event.event_type}] by {event.producer}. Priority: {event.priority.name}")

    def dispatch_next(self) -> Optional[BlackboardEvent]:
        if not self.queue:
            return None
        event = self.queue.pop(0)
        handlers = self.subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error executing handler for event {event.event_id}: {e}")
        return event

    def get_replay_log(self) -> List[Dict[str, Any]]:
        """Provides complete audit and debug capability for all cognitive steps."""
        return self.replay_buffer

    def clear(self) -> None:
        self.events_by_id.clear()
        self.queue.clear()
        self.replay_buffer.clear()
