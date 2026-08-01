from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.preferences_service import PreferencesService
from dto.preferences import ThemeConfigDTO

router = APIRouter()


def _get_preferences_service() -> PreferencesService:
    return PreferencesService()


@router.get("/preferences")
def get_preferences(user_id: int = Query(1, ge=1)):
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
def update_preferences(user_id: int = Query(1, ge=1), data: dict = {}):
    svc = _get_preferences_service()
    return svc.upsert_preferences(user_id, data)


@router.put("/preferences/theme")
def update_theme(user_id: int = Query(1, ge=1), theme: str = "dark"):
    svc = _get_preferences_service()
    return svc.update_theme(user_id, theme)


@router.put("/preferences/layout")
def update_layout(user_id: int = Query(1, ge=1), layout: dict = {}):
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
        "notification_preferences": {
            "trade_opened": True,
            "trade_closed": True,
            "signal_approved": True,
            "signal_rejected": False,
            "risk_warning": True,
            "system_alert": True,
        },
    }
