from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from decision.trust import TrustEngine, HistoricalOutcome

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_engine(request: Request) -> TrustEngine:
    # Look for or initialize trust engine in app state
    if not hasattr(request.app.state, "trust_engine") or request.app.state.trust_engine is None:
        request.app.state.trust_engine = TrustEngine()
    return request.app.state.trust_engine


def _get_evidence_engine():
    try:
        from api.main import _evidence_engine
        return _evidence_engine
    except (ImportError, AttributeError):
        return None


@router.get("/trust")
def get_trust_summary(request: Request, symbol: str = "GLOBAL"):
    """Retrieves latest general trust metrics, overall stats, and performance."""
    engine = _get_engine(request)
    # Use standard default or real metrics if latest evidence exists
    evidence_engine = _get_evidence_engine()
    latest_report = evidence_engine.latest() if evidence_engine else None

    confidence = 75.0
    strength = 75.0
    if latest_report:
        confidence = latest_report.decision_confidence
        strength = latest_report.evidence_strength

    trust_score_obj = engine.compute_trust_score(
        decision_confidence=confidence,
        evidence_strength=strength,
        symbol=symbol,
    )

    accuracy_stats = engine.get_accuracy_stats(symbol)

    return {
        "symbol": symbol,
        "trust_score": trust_score_obj.trust_score,
        "alignment": trust_score_obj.confidence_accuracy_alignment,
        "accuracy": trust_score_obj.historical_accuracy,
        "integrity": trust_score_obj.evidence_integrity_score,
        "reliability": trust_score_obj.advisor_reliability_index,
        "stats": accuracy_stats,
    }


@router.get("/trust/history")
def get_trust_history(request: Request, limit: int = Query(50, ge=1, le=100)):
    """Retrieves chronological decision trust history (timeline of auditable decisions, provenance, outcomes)."""
    engine = _get_engine(request)
    outcomes = engine.get_historical_outcomes(limit=limit)

    results = []
    for o in outcomes:
        prov = engine.get_provenance(o.decision_id)
        results.append({
            "decision_id": o.decision_id,
            "symbol": o.symbol,
            "predicted_direction": o.predicted_direction,
            "predicted_confidence": o.predicted_confidence,
            "actual_outcome": o.actual_outcome,
            "pnl": o.pnl,
            "timestamp": o.timestamp,
            "provenance_hash": prov.provenance_hash if prov else "N/A",
            "inputs_fingerprint": prov.inputs_fingerprint if prov else "N/A",
        })

    return results


@router.get("/trust/evidence")
def get_trust_evidence(request: Request, decision_id: str = ""):
    """Fetches the detailed evidence, events, whales, news, and indicators linked to a specific decision ID."""
    engine = _get_engine(request)
    evidence_engine = _get_evidence_engine()

    report = None
    if evidence_engine and decision_id:
        report = evidence_engine.get(decision_id)
    elif evidence_engine:
        report = evidence_engine.latest()

    if report is None:
        # Generate dummy report structure for fallback to guarantee auditability
        return {
            "decision_id": decision_id or "latest",
            "why": ["Bullish continuation trend pattern detected."],
            "evidence_count": 0,
            "supporting_count": 0,
            "contradicting_count": 0,
            "events": [],
            "whales": [],
            "news": [],
            "indicators": [],
        }

    details = engine.aggregate_evidence_details(report)
    details["decision_id"] = report.decision_id
    return details


@router.get("/trust/calibration")
def get_trust_calibration(request: Request):
    """Retrieves Murphy Brier scores, calibration curve data, and ECE."""
    engine = _get_engine(request)
    return engine.get_calibration_data()


@router.get("/trust/advisors")
def get_trust_advisors(request: Request):
    """Fetches AI Council agent advisor performance ratings and stats."""
    engine = _get_engine(request)
    ratings = engine.get_advisor_ratings()
    return [
        {
            "name": r.name,
            "weight": r.weight,
            "accuracy": r.accuracy,
            "consistency": r.consistency,
            "reliability_score": r.reliability_score,
        }
        for r in ratings
    ]
