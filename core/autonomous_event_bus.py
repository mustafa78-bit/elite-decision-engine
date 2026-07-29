from __future__ import annotations

import logging
import threading
from typing import Any, Callable, List

logger = logging.getLogger(__name__)


class AutonomousEventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._subscribers = []
                cls._instance._history = []
            return cls._instance

    def subscribe(self, callback: Callable[[Any], None]) -> None:
        with self._lock:
            self._subscribers.append(callback)

    def publish(self, event: Any) -> None:
        with self._lock:
            self._history.append(event)
            logger.info("TELEMETRY: [AutonomousEventBus] Published event: %s", event.__class__.__name__)
            # Notify subscribers
            for sub in self._subscribers:
                try:
                    sub(event)
                except Exception as e:
                    logger.error("Subscriber notification failed on event %s: %s", event, e)

    def get_history(self) -> List[Any]:
        with self._lock:
            return list(self._history)

    def clear(self) -> None:
        with self._lock:
            self._subscribers.clear()
            self._history.clear()
