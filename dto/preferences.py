from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class UserPreferencesDTO:
    timezone: str = "UTC"
    theme: str = "dark"
    dashboard_config: Optional[dict[str, Any]] = None
    risk_preferences: Optional[dict[str, Any]] = None
    layout_config: Optional[dict[str, Any]] = None
    notification_preferences: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThemeConfigDTO:
    theme: str = "dark"
    primary_color: str = "#3b82f6"
    secondary_color: str = "#8b5cf6"
    background_color: str = "#0f172a"
    surface_color: str = "#1e293b"
    text_color: str = "#f1f5f9"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LayoutConfigDTO:
    widget_order: Optional[list[str]] = None
    visible_widgets: Optional[list[str]] = None
    chart_layout: str = "grid"
    sidebar_collapsed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
