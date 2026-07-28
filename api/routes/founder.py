from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from decision.kernel.FounderOS import FounderOS
from decision.kernel.DecisionLedger import DecisionLedger
from decision.kernel.CalibrationEngine import CalibrationEngine
from decision.kernel.TrustMetrics import TrustMetrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/founder", tags=["founder"])

# Instantiate single global managers
_founder_os = FounderOS()
_ledger = DecisionLedger()
_calibration = CalibrationEngine(ledger=_ledger)
_trust = TrustMetrics(ledger=_ledger)


class QueryRequest(BaseModel):
    question: str


class ActionRequest(BaseModel):
    action_type: str
    details: dict[str, Any]


@router.get("/brief")
def get_morning_brief():
    """Generate the daily automatic Executive Morning Brief using calculated Ledger metrics."""
    try:
        # Generate calculated metrics
        cal_metrics = _calibration.calculate_metrics()
        trust_metrics = _trust.calculate_trust()

        # Ground morning brief in calculated ledger metrics
        brief = _founder_os.generate_brief()

        # Replace placeholders with dynamic metrics
        learning_summary = f"Win Rate holds at {trust_metrics['win_rate']}%. Expected return sits at {trust_metrics['expected_return']:.4f} per trade on average."
        calibration_summary = f"Murphy Brier calibration score is {cal_metrics['brier_score']:.4f}. Expected Calibration Error (ECE) is currently at {cal_metrics['calibration_error']*100:.2f}%."

        return {
            "status": "success",
            "brief": {
                "timestamp": brief.timestamp,
                "executive_summary": brief.executive_summary,
                "market_summary": brief.market_summary,
                "portfolio_summary": brief.portfolio_summary,
                "learning_summary": learning_summary,
                "calibration_summary": calibration_summary,
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
    """Answer an executive institutional memory question using real-time ledger records."""
    try:
        response = _founder_os.query(req.question)

        # Inject dynamic metrics if queried about decisions succeeding/failing or trust
        norm_key = req.question.lower().replace("?", "").replace(" ", "_").replace("'", "")
        if "succeeded" in norm_key or "failed" in norm_key or "trust" in norm_key:
            trust_metrics = _trust.calculate_trust()
            response["answer"] = f"Win Rate is currently {trust_metrics['win_rate']}%. Decision Accuracy is {trust_metrics['decision_accuracy']*100:.1f}%. Realized Return is {trust_metrics['realized_return']:.4f} USD."

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


@router.get("/calibration")
def get_calibration_metrics():
    """Retrieve system calibration error scores dynamically computed from the ledger."""
    return {
        "status": "success",
        "metrics": _calibration.calculate_metrics()
    }


@router.get("/trust")
def get_trust_metrics():
    """Retrieve performance-based trust metrics dynamically computed from the ledger."""
    return {
        "status": "success",
        "metrics": _trust.calculate_trust()
    }


@router.get("/replays/{decision_id}")
def get_decision_replay(decision_id: str):
    """Replay and reconstruct the complete context, evidence, and evaluation snapshot."""
    record = _ledger.get_record(decision_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Decision '{decision_id}' not found in ledger")
    return {
        "status": "success",
        "decision_id": decision_id,
        "reconstructed_decision": record
    }


@router.get("/explain/{decision_id}")
def query_decision_explain(decision_id: str):
    """Explain a decision: Why? What evidence? What confidence? What risks? What alternatives?"""
    record = _ledger.get_record(decision_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Decision '{decision_id}' not found in ledger")

    # Reconstruct non-hallucinated explanation from immutable ledger data
    confidence = record.get("confidence", 50.0)
    decision = record.get("decision", "REJECT")
    evidence_count = len(record.get("evidence", []))
    risk_score = record.get("risk_score", 0.3)
    side = record.get("side", "LONG")
    symbol = record.get("symbol", "BTC")

    why = f"The Decision Kernel recommended **{decision}** for {symbol} ({side}) based on a technical score of {record.get('score', 0.5):.2f}."

    # Identify alternatives
    alternatives = ["WATCH" if decision == "REJECT" else "REJECT", "HOLD_Allocation"]

    return {
        "status": "success",
        "decision_id": decision_id,
        "explanation": {
            "why": why,
            "evidence": f"Evaluation processed {evidence_count} technical and trust evidence pieces.",
            "confidence": f"Confidence was calibrated at {confidence:.1f}%.",
            "risks": f"Risk assessment reported risk_score of {risk_score:.2f}.",
            "alternatives": alternatives
        }
    }


def get_global_founder_os() -> FounderOS:
    """Dependency helper to resolve global FounderOS."""
    return _founder_os
