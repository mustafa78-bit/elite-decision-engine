from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from database import UserSettings, get_session

logger = logging.getLogger(__name__)


class PreferencesService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def get_preferences(self, user_id: int) -> Optional[dict[str, Any]]:
        session = self.session_factory()
        try:
            row = session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            if not row:
                return None
            return {
                "user_id": row.user_id,
                "timezone": row.timezone or "UTC",
                "theme": row.theme or "dark",
                "dashboard_config": row.dashboard_config or {},
                "risk_preferences": row.risk_preferences or {},
                "layout_config": row.layout_config or {},
                "notification_preferences": row.notification_preferences or {},
            }
        finally:
            session.close()

    def upsert_preferences(self, user_id: int, data: dict[str, Any]) -> dict[str, Any]:
        session = self.session_factory()
        try:
            row = session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            if not row:
                row = UserSettings(user_id=user_id)
                session.add(row)
            if "timezone" in data:
                row.timezone = data["timezone"]
            if "theme" in data:
                row.theme = data["theme"]
            if "dashboard_config" in data:
                row.dashboard_config = data["dashboard_config"]
            if "risk_preferences" in data:
                row.risk_preferences = data["risk_preferences"]
            if "layout_config" in data:
                row.layout_config = data["layout_config"]
            if "notification_preferences" in data:
                row.notification_preferences = data["notification_preferences"]
            session.commit()
            return self.get_preferences(user_id) or {}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_theme(self, user_id: int, theme: str) -> dict[str, Any]:
        return self.upsert_preferences(user_id, {"theme": theme})

    def update_layout(self, user_id: int, layout: dict[str, Any]) -> dict[str, Any]:
        return self.upsert_preferences(user_id, {"layout_config": layout})
