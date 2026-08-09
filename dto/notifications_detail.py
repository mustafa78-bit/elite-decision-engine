from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class NotificationDetailDTO:
    id: int | None = None
    user_id: int | None = None
    event_type: str = ""
    payload: dict[str, Any] | None = None
    read: bool = False
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationStatsDTO:
    total: int = 0
    unread: int = 0
    by_type: dict[str, int] | None = None
    last_seven_days: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationPreferenceDTO:
    # signal_approved/signal_rejected/risk_warning were removed -- they
    # referenced event categories that don't exist anywhere in
    # notifications/events.py and have no emit() call site in the backend.
    trade_opened: bool = True
    trade_closed: bool = True
    system_alert: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BulkNotificationActionDTO:
    notification_ids: list[int] | None = None
    mark_all_read: bool = False
    event_type_filter: str | None = None
