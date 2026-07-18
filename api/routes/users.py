import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from database import User, UserSettings, get_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/users/me")
def get_me(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "username": user.username, "email": user.email}
    finally:
        session.close()


class SettingsBody(BaseModel):
    timezone: str | None = None
    dashboard_config: dict | None = None
    risk_preferences: dict | None = None


@router.put("/users/settings")
def update_settings(body: SettingsBody, request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_session()
    try:
        settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id)
            session.add(settings)

        if body.timezone is not None:
            settings.timezone = body.timezone
        if body.dashboard_config is not None:
            settings.dashboard_config = body.dashboard_config
        if body.risk_preferences is not None:
            settings.risk_preferences = body.risk_preferences

        session.commit()
        return {"success": True, "settings": {
            "timezone": settings.timezone,
            "dashboard_config": settings.dashboard_config,
            "risk_preferences": settings.risk_preferences,
        }}
    except Exception as e:
        session.rollback()
        logger.error("Failed to update settings: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update settings")
    finally:
        session.close()


@router.get("/users/settings")
def get_settings(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_session()
    try:
        settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings:
            return {"timezone": "UTC", "dashboard_config": {}, "risk_preferences": {}}
        return {
            "timezone": settings.timezone,
            "dashboard_config": settings.dashboard_config,
            "risk_preferences": settings.risk_preferences,
        }
    finally:
        session.close()
