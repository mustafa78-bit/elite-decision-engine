from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from database import Signal, get_session

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_explanation_service():
    from services.explanation_service import ExplanationService
    from scoring.scoring_engine import ScoringEngine
    from core.confidence_engine import ConfidenceEngine
    from market_data.intelligence import IntelligenceCollector
    return ExplanationService(
        scoring_engine=ScoringEngine(),
        confidence_engine=ConfidenceEngine(),
        intelligence_collector=IntelligenceCollector(),
    )


@router.get("/explain/{signal_id}")
def explain_signal(signal_id: int, request: Request):
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        service = _get_explanation_service()
        explanation = service.explain_signal(signal)

        return {"signal_id": signal_id, "explanation": explanation.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Explanation failed for signal %s: %s", signal_id, e)
        return JSONResponse(status_code=500, content={"error": str(e), "signal_id": signal_id})
    finally:
        session.close()


@router.get("/explain/{signal_id}/reasoning")
def explain_reasoning(signal_id: int, request: Request):
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        service = _get_explanation_service()
        explanation = service.explain_signal(signal)
        if explanation.reasoning:
            return {"signal_id": signal_id, "reasoning": explanation.reasoning.to_dict()}
        return {"signal_id": signal_id, "reasoning": None}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Reasoning failed for signal %s: %s", signal_id, e)
        return JSONResponse(status_code=500, content={"error": str(e), "signal_id": signal_id})
    finally:
        session.close()


@router.get("/explain/{signal_id}/timeline")
def explain_timeline(signal_id: int, request: Request):
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        service = _get_explanation_service()
        explanation = service.explain_signal(signal)
        if explanation.timeline:
            return {"signal_id": signal_id, "timeline": explanation.timeline.to_dict()}
        return {"signal_id": signal_id, "timeline": None}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Timeline failed for signal %s: %s", signal_id, e)
        return JSONResponse(status_code=500, content={"error": str(e), "signal_id": signal_id})
    finally:
        session.close()


@router.get("/explain/{signal_id}/human")
def explain_human_readable(signal_id: int, request: Request):
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        service = _get_explanation_service()
        explanation = service.explain_signal(signal)
        human = ""
        if explanation.reasoning:
            human = explanation.reasoning.human_readable
        return {"signal_id": signal_id, "explanation": human}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Human-readable explanation failed for signal %s: %s", signal_id, e)
        return JSONResponse(status_code=500, content={"error": str(e), "signal_id": signal_id})
    finally:
        session.close()
