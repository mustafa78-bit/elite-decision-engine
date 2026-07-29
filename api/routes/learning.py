from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from database import get_session
from services.learning.decision_memory import DecisionMemoryService
from services.learning.pattern_discovery import PatternDiscoveryService
from services.learning.calibration_engine import CalibrationService
from services.learning.drift_detection import DriftDetectionEngine

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


@router.post("/sync")
def sync_memories():
    """
    Trigger synchronization of core decision records (Signals, Trades, Explanations)
    into the DecisionMemory persistent repository.
    """
    svc = DecisionMemoryService()
    count = svc.sync_memories()
    return {"status": "success", "synced": count}


@router.get("/dashboard")
def get_learning_dashboard():
    """
    Get aggregated high-level statistics of the Learning Intelligence Engine,
    including a dynamically compiled executive AI summary of learning status.
    """
    # Trigger a sync first to ensure up-to-date data
    mem_svc = DecisionMemoryService()
    mem_svc.sync_memories()

    cal_svc = CalibrationService()
    cal_rep = cal_svc.calculate_calibration()

    drift_eng = DriftDetectionEngine()
    drift_rep = drift_eng.detect_drift()

    pat_svc = PatternDiscoveryService()
    pat_rep = pat_svc.discover_patterns()

    # Calculate dominant pattern
    dom_profitable = pat_rep["profitable_patterns"][0]["name"] if pat_rep["profitable_patterns"] else "N/A"

    # Dynamically compile a short executive AI summary
    summary_text = (
        f"NEXUS has analyzed {cal_rep['total_decisions']} historical decisions. "
        f"Current calibration quality is graded as '{cal_rep['confidence_grade']}'. "
        f"The system has discovered {len(pat_rep['profitable_patterns'])} winning patterns and "
        f"{len(pat_rep['failure_patterns'])} repeated failure structures. "
        f"{'Strategic behavioral drift alerts are active for key DNA components.' if drift_rep['has_drift'] else 'No significant strategic behavioral drift has been detected.'}"
    )

    return {
        "ece": cal_rep["ece"],
        "brier_score": cal_rep["brier_score"],
        "total_decisions": cal_rep["total_decisions"],
        "calibration_status": cal_rep["calibration_status"],
        "confidence_grade": cal_rep["confidence_grade"],
        "has_drift": drift_rep["has_drift"],
        "active_drift_alerts_count": len(drift_rep["alerts"]),
        "dominant_profitable_pattern": dom_profitable,
        "executive_summary": summary_text,
    }


@router.get("/memories")
def list_memories(
    symbol: Optional[str] = Query(None, description="Filter by asset symbol"),
    side: Optional[str] = Query(None, description="Filter by side (LONG/SHORT)"),
    result: Optional[str] = Query(None, description="Filter by outcome (WIN/LOSS/PENDING)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Get paginated, filterable list of stored Decision Memories.
    """
    svc = DecisionMemoryService()
    svc.sync_memories()  # Auto-sync
    memories = svc.get_memories(symbol=symbol, side=side, result=result, limit=limit, offset=offset)
    return {
        "memories": memories,
        "limit": limit,
        "offset": offset,
    }


@router.get("/memories/{memory_id}")
def get_memory_detail(memory_id: str):
    """
    Get detail for a specific Decision Memory, including its top 5 similar historical decisions.
    """
    svc = DecisionMemoryService()
    mem = svc.get_memory(memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail=f"Decision memory '{memory_id}' not found")

    # Expose related historical decisions
    similar = svc.find_similar(memory_id, limit=5)

    return {
        "memory": mem,
        "similar_decisions": similar,
    }


@router.get("/memories/{memory_id}/similar")
def get_similar_memories(memory_id: str, limit: int = Query(5, ge=1, le=20)):
    """
    Retrieve top N most similar decisions based on our similarity search engine (Cosine Similarity).
    """
    svc = DecisionMemoryService()
    similar = svc.find_similar(memory_id, limit=limit)
    return {
        "target_id": memory_id,
        "similar_decisions": similar,
    }


@router.get("/patterns")
def get_patterns():
    """
    Retrieve discovered profitable recurring structures and repeated failure patterns.
    """
    mem_svc = DecisionMemoryService()
    mem_svc.sync_memories()  # Ensure data is synced
    svc = PatternDiscoveryService()
    return svc.discover_patterns()


@router.get("/calibration")
def get_calibration_report():
    """
    Get the detailed confidence calibration metrics (ECE, Brier, Bins, Diagnostics).
    """
    mem_svc = DecisionMemoryService()
    mem_svc.sync_memories()
    svc = CalibrationService()
    return svc.calculate_calibration()


@router.get("/drift")
def get_drift_report():
    """
    Get the detailed Decision DNA drift analysis (PSI, shift, active alerts).
    """
    mem_svc = DecisionMemoryService()
    mem_svc.sync_memories()
    svc = DriftDetectionEngine()
    return svc.detect_drift()


@router.get("/timeline")
def get_learning_timeline(limit: int = Query(50, ge=1, le=200)):
    """
    Get a chronological timeline of decision contexts and outcomes.
    """
    mem_svc = DecisionMemoryService()
    mem_svc.sync_memories()
    memories = mem_svc.get_memories(limit=limit)
    timeline = []
    for m in memories:
        timeline.append({
            "id": m["decision_id"],
            "symbol": m["symbol"],
            "side": m["side"],
            "pnl": m["outcome"].get("pnl", 0.0),
            "result": m["outcome"].get("result", "PENDING"),
            "confidence": m["decision_dna"].get("confidence", 50.0),
            "timestamp": m["created_at"],
        })
    return {
        "timeline": timeline,
    }
