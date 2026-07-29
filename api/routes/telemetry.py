from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.telemetry_service import TelemetryService

logger = logging.getLogger(__name__)
router = APIRouter()


class TelemetryEventCreate(BaseModel):
    screen: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=100)
    duration: Optional[float] = Field(None, ge=0.0)
    outcome: Optional[str] = Field(None, max_length=100)


def _get_telemetry_service() -> TelemetryService:
    return TelemetryService()


@router.post("/telemetry")
def track_telemetry_event(body: TelemetryEventCreate):
    """API endpoint to track product telemetry events."""
    try:
        svc = _get_telemetry_service()
        event = svc.track_event(
            screen=body.screen,
            action=body.action,
            duration=body.duration,
            outcome=body.outcome,
        )
        return {
            "status": "success",
            "event_id": event.id,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        }
    except Exception as e:
        logger.error("Failed to track telemetry in API: %s", e)
        raise HTTPException(status_code=500, detail="Failed to persist telemetry event")


@router.get("/telemetry")
def get_telemetry_stream(limit: int = Query(100, ge=1, le=500)):
    """API endpoint to retrieve unified event stream."""
    try:
        svc = _get_telemetry_service()
        events = svc.get_event_stream(limit=limit)
        return [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "screen": e.screen,
                "action": e.action,
                "duration": e.duration,
                "outcome": e.outcome,
            }
            for e in events
        ]
    except Exception as e:
        logger.error("Failed to fetch telemetry stream: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve telemetry events")
