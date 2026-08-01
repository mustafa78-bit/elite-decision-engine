from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class DashboardWidgetDTO:
    widget_id: str = ""
    widget_type: str = ""
    title: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KPIDashboardWidgetDTO:
    kpis: list[dict[str, Any]] = field(default_factory=list)
    period: str = "24h"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExplanationDashboardWidgetDTO:
    signal_id: int = 0
    decision: str = ""
    confidence: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)
    human_readable: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineDashboardWidgetDTO:
    events: list[dict[str, Any]] = field(default_factory=list)
    total_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PortfolioDashboardWidgetDTO:
    total_pnl: float = 0.0
    total_trades: int = 0
    open_trades: int = 0
    win_rate: float = 0.0
    equity: float = 0.0
    max_drawdown: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MonitoringDashboardWidgetDTO:
    status: str = "healthy"
    uptime_seconds: float = 0.0
    database_status: str = "connected"
    collector_status: str = "unknown"
    websocket_clients: int = 0
    last_error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationDashboardWidgetDTO:
    unread: int = 0
    total: int = 0
    notifications: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HeroBannerDTO:
    decision: str = "WAIT"
    confidence: float = 0.0
    risk: float = 0.0
    summary: str = ""
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    supporting_signals: list[str] = field(default_factory=list)
    entry: float = 0.0
    tp: float = 0.0
    sl: float = 0.0
    rr: float = 0.0
    timestamp: str = ""
    market_regime: str = "UNKNOWN"
    signal_id: int = 0
    symbol: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
