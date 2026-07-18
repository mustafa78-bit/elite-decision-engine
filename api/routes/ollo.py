from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from services.ollo.mission_profile import PROFILES_BY_ROOM

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_ollo() -> Optional:
    try:
        from api.main import _ollo_service
        return _ollo_service
    except (ImportError, AttributeError):
        return None


@router.get("/ollo/greet")
def ollo_greet(room: str = "command_deck", request: Request = None):
    svc = _get_ollo()
    if svc is None:
        return JSONResponse(status_code=503, content={"error": "OLLO not initialized"})
    try:
        response = svc.greet(room_id=room)
        return response.to_dict()
    except Exception as e:
        logger.error("OLLO greet failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/ollo/query")
def ollo_query(query: str, room: str = "command_deck", request: Request = None):
    if not query or not query.strip():
        return JSONResponse(status_code=400, content={"error": "Query is required"})
    svc = _get_ollo()
    if svc is None:
        return JSONResponse(status_code=503, content={"error": "OLLO not initialized"})
    try:
        response = svc.query(query=query.strip(), room_id=room)
        return response.to_dict()
    except Exception as e:
        logger.error("OLLO query failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/ollo/briefing")
def ollo_briefing(
    kind: str = "morning",
    room: str = "command_deck",
    request: Request = None,
):
    valid_kinds = ("morning", "evening", "market_update", "emergency", "mission")
    if kind not in valid_kinds:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid kind. Valid: {', '.join(valid_kinds)}"},
        )
    svc = _get_ollo()
    if svc is None:
        return JSONResponse(status_code=503, content={"error": "OLLO not initialized"})
    try:
        briefing = svc.briefing(kind=kind, room_id=room)
        return briefing.to_dict()
    except Exception as e:
        logger.error("OLLO briefing failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/ollo/status")
def ollo_status(request: Request = None):
    svc = _get_ollo()
    if svc is None:
        return {
            "provider": "unavailable",
            "model": "unavailable",
            "current_mission_profile": None,
            "current_room": None,
            "ai_health": {"connected": False, "latency_ms": 0, "error": "OLLO not initialized"},
            "memory": {"briefings_stored": 0, "recommendations_stored": 0, "preferences_count": 0},
            "available_rooms": list(PROFILES_BY_ROOM.keys()),
        }
    try:
        status = svc.status()
        status["available_rooms"] = list(PROFILES_BY_ROOM.keys())
        return status
    except Exception as e:
        logger.error("OLLO status failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
