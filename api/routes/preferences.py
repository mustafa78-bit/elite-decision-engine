from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from dto.preferences import ThemeConfigDTO
from services.preferences_service import PreferencesService

router = APIRouter()


def _get_preferences_service() -> PreferencesService:
    return PreferencesService()


def _require_user_id(request: Request) -> int:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.get("/preferences")
def get_preferences(request: Request):
    user_id = _require_user_id(request)
    svc = _get_preferences_service()
    result = svc.get_preferences(user_id)
    if result is None:
        return {
            "user_id": user_id, "timezone": "UTC", "theme": "dark",
            "dashboard_config": {}, "risk_preferences": {},
            "layout_config": {}, "notification_preferences": {},
        }
    return result


@router.put("/preferences")
def update_preferences(request: Request, data: dict = {}):
    user_id = _require_user_id(request)
    svc = _get_preferences_service()
    return svc.upsert_preferences(user_id, data)


@router.put("/preferences/theme")
def update_theme(request: Request, theme: str = "dark"):
    user_id = _require_user_id(request)
    svc = _get_preferences_service()
    return svc.update_theme(user_id, theme)


@router.put("/preferences/layout")
def update_layout(request: Request, layout: dict = {}):
    user_id = _require_user_id(request)
    svc = _get_preferences_service()
    return svc.update_layout(user_id, layout)


@router.get("/preferences/theme-config")
def get_theme_config(theme: str = Query("dark")):
    cfg = ThemeConfigDTO(theme=theme)
    return cfg.to_dict()


@router.get("/preferences/defaults")
def get_default_preferences():
    return {
        "timezone": "UTC",
        "theme": "dark",
        "dashboard_config": {
            "widget_order": ["kpi", "portfolio", "monitoring", "notifications"],
            "visible_widgets": ["kpi", "portfolio", "monitoring", "notifications", "explanation", "timeline"],
            "chart_layout": "grid",
            "sidebar_collapsed": False,
        },
        "risk_preferences": {
            "max_open_trades": 3,
            "max_daily_loss": 10000,
            "max_symbol_exposure": 0.3,
            "max_portfolio_exposure": 0.8,
        },
        "layout_config": {
            "widget_order": ["kpi", "portfolio", "monitoring", "notifications"],
            "visible_widgets": ["kpi", "portfolio", "monitoring", "notifications", "explanation", "timeline"],
            "chart_layout": "grid",
            "sidebar_collapsed": False,
        },
        # signal_approved/signal_rejected/risk_warning were removed --
        # they referenced event categories (SIGNAL_APPROVED, SIGNAL_REJECTED,
        # RISK_WARNING) that don't exist anywhere in notifications/events.py
        # and have no emit() call site in the backend at all. Only keys for
        # events that are actually ever emitted belong here; a toggle for a
        # non-existent event is pure misleading dead configuration.
        "notification_preferences": {
            "trade_opened": True,
            "trade_closed": True,
            "system_alert": True,
            "market_news": True,
            "vc_funding_news": True,
        },
    }
