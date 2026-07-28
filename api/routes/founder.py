from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from decision.kernel.FounderOS import FounderOS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/founder", tags=["founder"])

# Instantiate single global FounderOS manager
_founder_os = FounderOS()


class QueryRequest(BaseModel):
    question: str


class ActionRequest(BaseModel):
    action_type: str
    details: dict[str, Any]


@router.get("/brief")
def get_morning_brief():
    """Generate the daily automatic Executive Morning Brief."""
    try:
        brief = _founder_os.generate_brief()
        return {
            "status": "success",
            "brief": {
                "timestamp": brief.timestamp,
                "executive_summary": brief.executive_summary,
                "market_summary": brief.market_summary,
                "portfolio_summary": brief.portfolio_summary,
                "learning_summary": brief.learning_summary,
                "calibration_summary": brief.calibration_summary,
                "discovery_summary": brief.discovery_summary,
                "risk_summary": brief.risk_summary,
                "macro_summary": brief.macro_summary,
                "recommended_actions": brief.recommended_actions,
                "todays_priorities": brief.todays_priorities,
            }
        }
    except Exception as e:
        logger.exception("Failed to generate morning brief")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
def post_executive_query(req: QueryRequest):
    """Answer an executive institutional memory question."""
    try:
        response = _founder_os.query(req.question)
        # Record this action as an executive query
        _founder_os.record_executive_action({
            "action": f"Query: {req.question}",
            "response_snippet": response.get("answer", "")[:100],
        })
        return {
            "status": "success",
            "query": req.question,
            "response": response
        }
    except Exception as e:
        logger.exception("Failed to execute query")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action")
def record_executive_action(req: ActionRequest):
    """Record an executive preference or manual decision action."""
    try:
        _founder_os.record_executive_action({
            "action_type": req.action_type,
            "details": req.details,
        })
        return {
            "status": "success",
            "message": f"Successfully registered executive action: {req.action_type}"
        }
    except Exception as e:
        logger.exception("Failed to record executive action")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
def get_institutional_memory():
    """Retrieve the entire persistent Founder institutional memory log."""
    try:
        return {
            "status": "success",
            "memory": _founder_os.memory
        }
    except Exception as e:
        logger.exception("Failed to retrieve institutional memory")
        raise HTTPException(status_code=500, detail=str(e))


def get_global_founder_os() -> FounderOS:
    """Dependency helper to resolve global FounderOS."""
    return _founder_os
