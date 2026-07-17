import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from core.cache import TTLCache
from dto.models import NotificationDTO, AlertSummaryDTO


_NOTIFICATION_CATEGORIES = frozenset({
    "general", "trade", "signal", "system", "risk", "intelligence", "module",
})

_PRIORITY_LEVELS = frozenset({0, 1, 2, 3, 4, 5})


class NotificationService:

    def __init__(self, max_history: int = 1000, cache_ttl: float = 15.0):
        self._history: List[NotificationDTO] = []
        self._max_history = max_history
        self._cache = TTLCache(default_ttl=cache_ttl)
        self._on_new_notification: Optional[Callable] = None
        self._diagnostics: Dict[str, Any] = {
            "total_created": 0,
            "total_read": 0,
            "cache_hits": 0,
        }

    def set_callback(self, callback: Callable) -> None:
        self._on_new_notification = callback

    def notify(
        self,
        type: str = "info",
        category: str = "general",
        title: str = "",
        message: str = "",
        severity: str = "low",
        priority: int = 0,
    ) -> NotificationDTO:
        if category not in _NOTIFICATION_CATEGORIES:
            category = "general"
        priority = max(0, min(5, priority))
        notif = NotificationDTO(
            id=uuid.uuid4().hex[:12],
            type=type,
            category=category,
            title=title,
            message=message,
            severity=severity,
            priority=priority,
            read=False,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._history.append(notif)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        self._diagnostics["total_created"] += 1
        self._cache.invalidate("alert_summary")
        if self._on_new_notification:
            try:
                self._on_new_notification(notif)
            except Exception:
                pass
        return notif

    def get_history(
        self,
        limit: int = 50,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        unread_only: bool = False,
        min_priority: Optional[int] = None,
    ) -> List[NotificationDTO]:
        filtered = list(self._history)
        if category:
            filtered = [n for n in filtered if n.category == category]
        if severity:
            filtered = [n for n in filtered if n.severity == severity]
        if unread_only:
            filtered = [n for n in filtered if not n.read]
        if min_priority is not None:
            filtered = [n for n in filtered if n.priority >= min_priority]
        return filtered[-limit:]

    def mark_read(self, notification_id: str) -> bool:
        for n in self._history:
            if n.id == notification_id and not n.read:
                n.read = True
                self._diagnostics["total_read"] += 1
                self._cache.invalidate("alert_summary")
                return True
        return False

    def mark_all_read(self) -> int:
        count = 0
        for n in self._history:
            if not n.read:
                n.read = True
                count += 1
        if count:
            self._diagnostics["total_read"] += count
            self._cache.invalidate("alert_summary")
        return count

    def get_alert_summary(self) -> AlertSummaryDTO:
        cached = self._cache.get("alert_summary")
        if cached is not None:
            self._diagnostics["cache_hits"] += 1
            return cached
        total = len(self._history)
        unread = sum(1 for n in self._history if not n.read)
        critical = sum(1 for n in self._history if n.severity == "critical" and not n.read)
        warning = sum(1 for n in self._history if n.severity == "warning" and not n.read)
        info = sum(1 for n in self._history if n.severity == "info" and not n.read)
        by_category: Dict[str, int] = {}
        for n in self._history:
            if not n.read:
                by_category[n.category] = by_category.get(n.category, 0) + 1
        summary = AlertSummaryDTO(
            total=total, unread=unread,
            critical=critical, warning=warning, info=info,
            by_category=by_category,
        )
        self._cache.set("alert_summary", summary)
        return summary

    def get_categories(self) -> List[str]:
        return sorted(_NOTIFICATION_CATEGORIES)

    def get_priority_levels(self) -> List[int]:
        return sorted(_PRIORITY_LEVELS)

    def get_unread_count(self) -> int:
        return sum(1 for n in self._history if not n.read)

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            **self._diagnostics,
            "history_size": len(self._history),
            "unread_count": self.get_unread_count(),
        }

    def invalidate_cache(self) -> None:
        self._cache.invalidate("alert_summary")
