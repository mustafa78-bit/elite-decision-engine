from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from database import Signal, get_session

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_coordinator() -> Any:
    from services.coordinator_service import CoordinatorService
    return CoordinatorService()


@router.get("/coordinate/sources")
def list_intelligence_sources(request: Request):
    try:
        coordinator = _get_coordinator()
        sources = coordinator.intelligence_registry.list_sources()
        return {"sources": sources}
    except Exception as e:
        logger.error("List sources failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/coordinate/diagnostics")
def coordinator_diagnostics(request: Request):
    try:
        coordinator = _get_coordinator()
        diag = coordinator._build_diagnostics()
        return {"diagnostics": diag.to_dict()}
    except Exception as e:
        logger.error("Coordinator diagnostics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/coordinate/sources/register")
def register_source(
    name: str,
    source_type: str = "scoring",
    weight: float = 1.0,
    priority: int = 0,
    request: Request = None,
):
    try:
        coordinator = _get_coordinator()
        coordinator.intelligence_registry.register(
            name=name,
            source_type=source_type,
            instance=None,
            weight=weight,
            priority=priority,
        )
        return {"status": "registered", "name": name}
    except Exception as e:
        logger.error("Register source failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/coordinate/{signal_id}")
def coordinate_signal(signal_id: int, request: Request):
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        coordinator = _get_coordinator()
        report = coordinator.evaluate(signal)

        return {"signal_id": signal_id, "report": report.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Coordination failed for signal %s: %s", signal_id, e)
        return JSONResponse(status_code=500, content={"error": str(e), "signal_id": signal_id})
    finally:
        session.close()


@router.get("/coordinate/{signal_id}/consensus")
def consensus_for_signal(signal_id: int, request: Request):
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        coordinator = _get_coordinator()
        report = coordinator.evaluate(signal)
        if report.consensus:
            return {"signal_id": signal_id, "consensus": report.consensus.to_dict()}
        return {"signal_id": signal_id, "consensus": None}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Consensus failed for signal %s: %s", signal_id, e)
        return JSONResponse(status_code=500, content={"error": str(e), "signal_id": signal_id})

