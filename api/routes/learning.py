from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from database import (
    get_session,
    LearningOutcome,
    LearningPattern,
    AdvisorLearningHistory,
    LearningHistoryEntry,
)
from decision.learning import (
    OutcomeAnalyzer,
    PatternLearningEngine,
    HistoricalSimilarityEngine,
    StrategyPerformanceAnalyzer,
    AdvisorLearningModule,
    LearningReplayEngine,
    LearningTimeline,
    LearningDashboardEngine,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning", tags=["Learning Engine"])


def get_db():
    """Dependency provider that yields a database session. Resolves get_session at runtime for testing compatibility."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


# ─── GET /learning ────────────────────────────────────────────────────────

@router.get("")
def get_learning_summary(
    replay_id: str = Query("INITIAL", description="Replay session identifier"),
    session: Session = Depends(get_db)
):
    """Returns a high-level summary of the learning engine status, overall performance, and current weights."""
    try:
        perf_analyzer = StrategyPerformanceAnalyzer()
        perf = perf_analyzer.analyze_performance(session, replay_id=replay_id)

        adv_module = AdvisorLearningModule()
        weights = adv_module.get_current_weights(session)

        total_outcomes = session.query(LearningOutcome).filter(LearningOutcome.replay_id == replay_id).count()
        total_patterns = session.query(LearningPattern).count()

        return {
            "status": "ACTIVE",
            "replay_id": replay_id,
            "total_outcomes": total_outcomes,
            "total_patterns": total_patterns,
            "advisor_weights": weights,
            "performance": perf
        }
    except Exception as e:
        logger.error("Failed to get learning summary: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /learning/history ────────────────────────────────────────────────

@router.get("/history")
def get_learning_history(
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_db)
):
    """Retrieves chronological learning history timeline entries."""
    try:
        timeline = LearningTimeline()
        entries = timeline.get_history(session, limit=limit)
        return {
            "history": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "description": e.description,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None
                }
                for e in entries
            ]
        }
    except Exception as e:
        logger.error("Failed to get learning history: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /learning/patterns ────────────────────────────────────────────────

@router.get("/patterns")
def get_learning_patterns(
    pattern_type: Optional[str] = Query(None, pattern="^(SUCCESS|FAILURE)$"),
    replay_id: str = Query("INITIAL", description="Replay session identifier"),
    session: Session = Depends(get_db)
):
    """Retrieves all active success and failure patterns with supporting evidence."""
    try:
        q = session.query(LearningPattern).filter(LearningPattern.replay_id == replay_id)
        if pattern_type:
            q = q.filter(LearningPattern.pattern_type == pattern_type.upper())
        patterns = q.all()

        return {
            "patterns": [
                {
                    "id": p.id,
                    "pattern_type": p.pattern_type,
                    "name": p.name,
                    "description": p.description,
                    "historical_frequency": p.historical_frequency,
                    "historical_precision": p.historical_precision,
                    "supporting_decisions": p.supporting_decisions,
                    "supporting_events": p.supporting_events,
                    "related_graph_nodes": p.related_graph_nodes,
                    "related_projections": p.related_projections,
                    "confidence": p.confidence,
                    "trust": p.trust,
                    "conditions": p.conditions,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                }
                for p in patterns
            ]
        }
    except Exception as e:
        logger.error("Failed to get learning patterns: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /learning/outcomes ────────────────────────────────────────────────

@router.get("/outcomes")
def get_learning_outcomes(
    symbol: Optional[str] = Query(None, min_length=1, max_length=20),
    final_outcome: Optional[str] = Query(None, pattern="^(CORRECT|INCORRECT|PENDING)$"),
    replay_id: str = Query("INITIAL"),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_db)
):
    """Retrieves analyzed outcomes of trading decisions and signals."""
    try:
        q = session.query(LearningOutcome).filter(LearningOutcome.replay_id == replay_id)
        if symbol:
            q = q.filter(LearningOutcome.symbol == symbol.upper())
        if final_outcome:
            q = q.filter(LearningOutcome.final_outcome == final_outcome.upper())

        outcomes = q.order_by(LearningOutcome.timestamp.desc()).limit(limit).all()

        return {
            "outcomes": [
                {
                    "id": o.id,
                    "decision_id": o.decision_id,
                    "strategy": o.strategy,
                    "advisor_set": o.advisor_set,
                    "final_outcome": o.final_outcome,
                    "pnl": o.pnl,
                    "roi": o.roi,
                    "success_score": o.success_score,
                    "time_horizon": o.time_horizon,
                    "confidence_at_decision": o.confidence_at_decision,
                    "trust_at_decision": o.trust_at_decision,
                    "market_regime": o.market_regime,
                    "replay_id": o.replay_id,
                    "symbol": o.symbol,
                    "features": o.features,
                    "timestamp": o.timestamp.isoformat() if o.timestamp else None
                }
                for o in outcomes
            ]
        }
    except Exception as e:
        logger.error("Failed to get learning outcomes: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /learning/advisors ────────────────────────────────────────────────

@router.get("/advisors")
def get_advisor_learning(
    advisor_name: Optional[str] = Query(None, min_length=1, max_length=50),
    session: Session = Depends(get_db)
):
    """Retrieves independent learning and weight evolution history for advisors."""
    try:
        q = session.query(AdvisorLearningHistory)
        if advisor_name:
            q = q.filter(AdvisorLearningHistory.advisor_name == advisor_name)
        history = q.order_by(AdvisorLearningHistory.created_at.desc()).all()

        return {
            "advisors": [
                {
                    "id": h.id,
                    "advisor_name": h.advisor_name,
                    "win_rate": h.win_rate,
                    "historical_accuracy": h.historical_accuracy,
                    "precision": h.precision,
                    "recall": h.recall,
                    "average_confidence": h.average_confidence,
                    "calibration_trend": h.calibration_trend,
                    "weight_evolution": h.weight_evolution,
                    "learning_timeline": h.learning_timeline,
                    "created_at": h.created_at.isoformat() if h.created_at else None
                }
                for h in history
            ]
        }
    except Exception as e:
        logger.error("Failed to get advisor learning metrics: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST /learning/replay ─────────────────────────────────────────────────

@router.post("/replay")
def trigger_learning_replay(
    mode: str = Query("FULL", pattern="^(FULL|INCREMENTAL|SNAPSHOT|RECONSTRUCT)$"),
    replay_id: str = Query("INITIAL", min_length=1, max_length=100),
    snapshot_time: Optional[str] = Query(None),
    session: Session = Depends(get_db)
):
    """Triggers deterministic learning replay. Recreates all models from immutable raw log history."""
    try:
        replay_engine = LearningReplayEngine()

        if mode == "FULL":
            result = replay_engine.replay_from_scratch(session, replay_id=replay_id)
        elif mode == "INCREMENTAL":
            result = replay_engine.incremental_replay(session, replay_id=replay_id)
        elif mode == "SNAPSHOT":
            if not snapshot_time:
                raise HTTPException(status_code=400, detail="snapshot_time query param is required for SNAPSHOT mode")
            try:
                dt = datetime.fromisoformat(snapshot_time)
            except ValueError:
                raise HTTPException(status_code=400, detail="snapshot_time must be in ISO format")
            result = replay_engine.snapshot_replay(session, snapshot_time=dt, replay_id=replay_id)
        else: # RECONSTRUCT or custom comparison
            result = replay_engine.replay_from_scratch(session, replay_id=replay_id)

        session.commit()
        return result
    except Exception as e:
        session.rollback()
        logger.error("Learning replay failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /learning/dashboard ───────────────────────────────────────────────

@router.get("/dashboard")
def get_learning_dashboard(
    replay_id: str = Query("INITIAL"),
    session: Session = Depends(get_db)
):
    """Returns interpreted insights, trends, and learning workspace statistics."""
    try:
        engine = LearningDashboardEngine()
        dashboard = engine.compile_interpreted_dashboard(session, replay_id=replay_id)
        return dashboard
    except Exception as e:
        logger.error("Failed to compile learning dashboard: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
