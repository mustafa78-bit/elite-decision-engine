from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class IntelligenceRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._registry = {}
            return cls._instance

    def register(self, name: str, service_callable: Callable[[Any], Any]) -> None:
        with self._lock:
            self._registry[name] = service_callable
            logger.info("TELEMETRY: [IntelligenceRegistry] Registered intelligence service: %s", name)

    def get_service(self, name: str) -> Callable[[Any], Any] | None:
        with self._lock:
            return self._registry.get(name)

    def get_all_registered_names(self) -> List[str]:
        with self._lock:
            return list(self._registry.keys())

    def clear(self) -> None:
        with self._lock:
            self._registry.clear()
