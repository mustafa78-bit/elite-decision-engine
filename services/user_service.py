import uuid
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.cache import TTLCache
from dto.models import SerializableMixin
from dataclasses import dataclass, field, asdict


@dataclass
class UserPreferencesDTO(SerializableMixin):
    theme: str = "dark"
    language: str = "en"
    notifications_enabled: bool = True
    notification_types: Dict[str, bool] = field(default_factory=lambda: {
        "trade": True, "signal": True, "system": True, "risk": True,
    })
    dashboard_layout: str = "default"
    dashboard_preset: str = "default"
    favorite_symbols: List[str] = field(default_factory=list)
    watchlist: List[str] = field(default_factory=list)


@dataclass
class LayoutConfigDTO(SerializableMixin):
    id: str = ""
    name: str = ""
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    is_default: bool = False


@dataclass
class PresetDTO(SerializableMixin):
    id: str = ""
    name: str = ""
    description: str = ""
    layout: str = "default"
    widgets: List[str] = field(default_factory=list)


@dataclass
class RecentActivityDTO(SerializableMixin):
    id: str = ""
    action: str = ""
    description: str = ""
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMetadataDTO(SerializableMixin):
    session_id: str = ""
    started_at: str = ""
    last_active: str = ""
    ip_address: str = ""
    user_agent: str = ""
    request_count: int = 0


_MAX_RECENT_ACTIVITY = 100


class UserService:
    def __init__(self, cache_ttl: float = 60.0):
        self._preferences: Dict[str, UserPreferencesDTO] = {}
        self._layouts: Dict[str, List[LayoutConfigDTO]] = {}
        self._presets: List[PresetDTO] = self._default_presets()
        self._recent_activity: List[RecentActivityDTO] = []
        self._sessions: Dict[str, SessionMetadataDTO] = {}
        self._user_favorites: Dict[str, List[str]] = {}
        self._user_watchlists: Dict[str, List[str]] = {}
        self._cache = TTLCache(default_ttl=cache_ttl)
        self._diagnostics: Dict[str, Any] = {
            "total_users": 0,
            "total_sessions": 0,
            "total_activities": 0,
        }

    def _default_presets(self) -> List[PresetDTO]:
        return [
            PresetDTO(id="default", name="Default", description="Standard trading dashboard", layout="default", widgets=["portfolio", "intelligence", "risk", "monitoring"]),
            PresetDTO(id="trader", name="Trader", description="Focused on portfolio and trades", layout="compact", widgets=["portfolio", "trades", "risk"]),
            PresetDTO(id="analyst", name="Analyst", description="Deep intelligence analysis", layout="wide", widgets=["intelligence", "market", "signals", "whale"]),
            PresetDTO(id="minimal", name="Minimal", description="Clean and simple overview", layout="minimal", widgets=["overview", "notifications"]),
        ]

    def get_preferences(self, user_id: str) -> UserPreferencesDTO:
        if user_id not in self._preferences:
            self._preferences[user_id] = UserPreferencesDTO()
            self._diagnostics["total_users"] += 1
        return self._preferences[user_id]

    def update_preferences(self, user_id: str, updates: Dict[str, Any]) -> UserPreferencesDTO:
        prefs = self.get_preferences(user_id)
        for key, value in updates.items():
            if hasattr(prefs, key) and key != "favorite_symbols" and key != "watchlist":
                setattr(prefs, key, value)
        if "favorite_symbols" in updates:
            prefs.favorite_symbols = list(updates["favorite_symbols"])
        if "watchlist" in updates:
            prefs.watchlist = list(updates["watchlist"])
        self._cache.invalidate(f"prefs_{user_id}")
        return prefs

    def set_theme(self, user_id: str, theme: str) -> bool:
        if theme not in ("dark", "light", "system"):
            return False
        prefs = self.get_preferences(user_id)
        prefs.theme = theme
        self._cache.invalidate(f"prefs_{user_id}")
        return True

    def set_language(self, user_id: str, language: str) -> bool:
        prefs = self.get_preferences(user_id)
        prefs.language = language[:10]
        self._cache.invalidate(f"prefs_{user_id}")
        return True

    def set_notification_preferences(self, user_id: str, enabled: bool, types: Optional[Dict[str, bool]] = None) -> UserPreferencesDTO:
        prefs = self.get_preferences(user_id)
        prefs.notifications_enabled = enabled
        if types:
            for k, v in types.items():
                if k in prefs.notification_types:
                    prefs.notification_types[k] = v
        self._cache.invalidate(f"prefs_{user_id}")
        return prefs

    def get_layouts(self, user_id: str) -> List[Dict[str, Any]]:
        return [l.to_dict() for l in self._layouts.get(user_id, [])]

    def save_layout(self, user_id: str, name: str, widgets: List[Dict[str, Any]]) -> LayoutConfigDTO:
        if user_id not in self._layouts:
            self._layouts[user_id] = []
        layout = LayoutConfigDTO(
            id=uuid.uuid4().hex[:8],
            name=name,
            widgets=widgets,
            is_default=len(self._layouts[user_id]) == 0,
        )
        self._layouts[user_id].append(layout)
        return layout

    def delete_layout(self, user_id: str, layout_id: str) -> bool:
        layouts = self._layouts.get(user_id, [])
        for i, l in enumerate(layouts):
            if l.id == layout_id:
                layouts.pop(i)
                return True
        return False

    def get_presets(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._presets]

    def set_active_preset(self, user_id: str, preset_id: str) -> bool:
        valid_ids = {p.id for p in self._presets}
        if preset_id not in valid_ids:
            return False
        prefs = self.get_preferences(user_id)
        prefs.dashboard_preset = preset_id
        return True

    def add_favorite(self, user_id: str, symbol: str) -> List[str]:
        if user_id not in self._user_favorites:
            self._user_favorites[user_id] = []
        clean = symbol.strip().upper()
        if clean and clean not in self._user_favorites[user_id]:
            self._user_favorites[user_id].append(clean)
        return list(self._user_favorites[user_id])

    def remove_favorite(self, user_id: str, symbol: str) -> List[str]:
        clean = symbol.strip().upper()
        if user_id in self._user_favorites:
            self._user_favorites[user_id] = [s for s in self._user_favorites[user_id] if s != clean]
        return list(self._user_favorites.get(user_id, []))

    def get_favorites(self, user_id: str) -> List[str]:
        return list(self._user_favorites.get(user_id, []))

    def add_to_watchlist(self, user_id: str, symbol: str) -> List[str]:
        if user_id not in self._user_watchlists:
            self._user_watchlists[user_id] = []
        clean = symbol.strip().upper()
        if clean and clean not in self._user_watchlists[user_id]:
            self._user_watchlists[user_id].append(clean)
        return list(self._user_watchlists[user_id])

    def remove_from_watchlist(self, user_id: str, symbol: str) -> List[str]:
        clean = symbol.strip().upper()
        if user_id in self._user_watchlists:
            self._user_watchlists[user_id] = [s for s in self._user_watchlists[user_id] if s != clean]
        return list(self._user_watchlists.get(user_id, []))

    def get_watchlist(self, user_id: str) -> List[str]:
        return list(self._user_watchlists.get(user_id, []))

    def record_activity(self, user_id: str, action: str, description: str = "", metadata: Optional[Dict[str, Any]] = None) -> RecentActivityDTO:
        activity = RecentActivityDTO(
            id=uuid.uuid4().hex[:12],
            action=action,
            description=description,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )
        self._recent_activity.append(activity)
        self._diagnostics["total_activities"] += 1
        if len(self._recent_activity) > _MAX_RECENT_ACTIVITY:
            self._recent_activity = self._recent_activity[-_MAX_RECENT_ACTIVITY:]
        return activity

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._recent_activity[-limit:]]

    def create_session(self, user_id: str, ip_address: str = "", user_agent: str = "") -> SessionMetadataDTO:
        session = SessionMetadataDTO(
            session_id=uuid.uuid4().hex[:16],
            started_at=datetime.now(timezone.utc).isoformat(),
            last_active=datetime.now(timezone.utc).isoformat(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._sessions[user_id] = session
        self._diagnostics["total_sessions"] += 1
        return session

    def get_session(self, user_id: str) -> Optional[SessionMetadataDTO]:
        return self._sessions.get(user_id)

    def update_session_activity(self, user_id: str) -> None:
        session = self._sessions.get(user_id)
        if session:
            session.last_active = datetime.now(timezone.utc).isoformat()
            session.request_count += 1

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            **self._diagnostics,
            "preferences_count": len(self._preferences),
            "layouts_count": sum(len(v) for v in self._layouts.values()),
            "recent_activity_count": len(self._recent_activity),
        }
