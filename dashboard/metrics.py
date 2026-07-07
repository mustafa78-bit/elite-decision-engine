from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self) -> None:
        self._start_time = datetime.now(timezone.utc)
        self._request_count: int = 0

    @property
    def uptime_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self._start_time).total_seconds()

    @property
    def request_count(self) -> int:
        return self._request_count

    def increment_requests(self) -> None:
        self._request_count += 1

    def snapshot(self) -> dict:
        return {
            "uptime_seconds": round(self.uptime_seconds, 2),
            "request_count": self.request_count,
        }
