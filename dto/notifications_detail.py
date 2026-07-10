from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Optional


@dataclass
class NotificationDetailDTO:
    id: Optional[int] = None
    user_id: Optional[int] = None
    event_type: str = ""
    payload: Optional[dict[str, Any]] = None
    read: bool = False
    created_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationStatsDTO:
    total: int = 0
    unread: int = 0
    by_type: Optional[dict[str, int]] = None
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
    notification_ids: Optional[list[int]] = None
    mark_all_read: bool = False
    event_type_filter: Optional[str] = None
