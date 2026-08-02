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
    trade_opened: bool = True
    trade_closed: bool = True
    signal_approved: bool = True
    signal_rejected: bool = False
    risk_warning: bool = True
    system_alert: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BulkNotificationActionDTO:
    notification_ids: list[int] | None = None
    mark_all_read: bool = False
    event_type_filter: str | None = None
