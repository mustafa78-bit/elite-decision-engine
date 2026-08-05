from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class UserPreferencesDTO:
    timezone: str = "UTC"
    theme: str = "dark"
    dashboard_config: dict[str, Any] | None = None
    risk_preferences: dict[str, Any] | None = None
    layout_config: dict[str, Any] | None = None
    notification_preferences: dict[str, Any] | None = None

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
    widget_order: list[str] | None = None
    visible_widgets: list[str] | None = None
    chart_layout: str = "grid"
    sidebar_collapsed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
