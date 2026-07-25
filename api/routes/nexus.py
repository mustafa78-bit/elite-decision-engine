import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import Signal, get_session
from services.nexus_service import NexusService

logger = logging.getLogger(__name__)
router = APIRouter()


class QueryPayload(BaseModel):
    symbol: str = "BTC"
    timeframe: str = "1h"
    side: str = "LONG"


def _get_nexus_service() -> NexusService:
    return NexusService()


@router.get("/nexus/overview")
async def get_nexus_overview(
    symbol: str = Query("BTC", min_length=1, max_length=20)
):
    """Provides a unified coherent market intelligence overview from all 9 systems."""
    try:
        svc = _get_nexus_service()
        report = await svc.get_nexus_summary(symbol=symbol)
        return report
    except Exception as e:
        logger.exception("Nexus overview failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nexus/briefing")
async def get_nexus_briefing(
    symbol: str = Query("BTC", min_length=1, max_length=20)
):
    """Provides a structured high-level executive update briefing of the current terminal state."""
    try:
        svc = _get_nexus_service()
        report = await svc.get_nexus_summary(symbol=symbol)
        orchestrated = report.get("orchestrated_data", {})

        briefing = {
            "title": f"NEXUS EXECUTIVE BRIEFING - {symbol.upper()}",
            "market_summary": orchestrated.get("why", {}).get("explanation", ""),
            "tactical_triggers": orchestrated.get("why_now", {}).get("explanation", ""),
            "risk_assessment": orchestrated.get("risk", {}).get("explanation", ""),
            "recommendation_summary": orchestrated.get("final_recommendation", {}).get("explanation", ""),
            "availability": report.get("availability", {}),
            "timestamp": report.get("timestamp")
        }
        return briefing
    except Exception as e:
        logger.exception("Nexus briefing failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nexus/mission")
async def get_nexus_mission(
    symbol: str = Query("BTC", min_length=1, max_length=20)
):
    """Provides unified mission parameters mapping execution states, active targets, and subsystem readiness."""
    try:
        svc = _get_nexus_service()
        report = await svc.get_nexus_summary(symbol=symbol)
        orchestrated = report.get("orchestrated_data", {})

        mission = {
            "mission_id": f"nexus_mission_{symbol.lower()}",
            "symbol": symbol.upper(),
            "subsystem_readiness": report.get("availability", {}),
            "mission_status": "ACTIVE" if report.get("availability", {}).get("council") == "ONLINE" else "DEGRADED",
            "targets": orchestrated.get("final_recommendation", {}).get("details", {}).get("targets", {}),
            "invalidation_parameters": orchestrated.get("invalidation", {}).get("explanation", ""),
            "confidence_metric": orchestrated.get("confidence", {}).get("details", {}).get("confidence_percentage", 50.0),
            "timestamp": report.get("timestamp")
        }
        return mission
    except Exception as e:
        logger.exception("Nexus mission failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nexus/explain/{signal_id}")
async def get_nexus_explain(signal_id: int):
    """Explains an exact Signal ID through the unified NEXUS intelligence layer."""
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        svc = _get_nexus_service()
        report = await svc.get_nexus_summary(symbol=signal.symbol)

        # Override recommendation details with the specific signal context
        orchestrated = report.get("orchestrated_data", {})
        rec_details = orchestrated.get("final_recommendation", {}).get("details", {})
        rec_details["targets"]["entry"] = signal.price if signal.price else rec_details["targets"]["entry"]
        rec_details["action"] = signal.side if signal.side else rec_details["action"]

        return {
            "signal_id": signal_id,
            "orchestrated_data": orchestrated,
            "availability": report.get("availability"),
            "timestamp": report.get("timestamp")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Nexus explain failed for signal %s", signal_id)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/nexus/query")
async def post_nexus_query(payload: QueryPayload):
    """Processes user dynamic workspace queries and evaluates the target symbol context."""
    try:
        svc = _get_nexus_service()
        report = await svc.get_nexus_summary(symbol=payload.symbol)

        return {
            "query": {
                "symbol": payload.symbol,
                "timeframe": payload.timeframe,
                "side": payload.side
            },
            "orchestrated_data": report.get("orchestrated_data"),
            "availability": report.get("availability"),
            "timestamp": report.get("timestamp")
        }
    except Exception as e:
        logger.exception("Nexus query failed")
        raise HTTPException(status_code=500, detail=str(e))
