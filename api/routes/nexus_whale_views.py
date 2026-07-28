import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from database import get_session
from memory.l1_views.registry import global_registry
from memory.l1_views.runner import ProjectionRunner, ReplayCursor
from memory.l1_views.models import WhaleView, ProjectionState

router = APIRouter(prefix="/nexus/l1/whale", tags=["NEXUS Whale Materialized View"])


# Pydantic Schemas
class WhaleReplayRequest(BaseModel):
    start_seq_id: int = Field(..., ge=1, description="Sequence ID to start replaying from")
    end_seq_id: Optional[int] = Field(None, ge=1, description="Sequence ID to stop replaying at")


class WhaleRebuildResponse(BaseModel):
    status: str
    events_processed: int
    failed_events: int
    rebuild_duration: float
    replay_speed: float


class WhaleViewSchema(BaseModel):
    wallet_id: str
    total_events: int
    accumulation_score: float
    distribution_score: float
    realized_accuracy: float
    trust_score: float
    last_activity: Optional[str] = None
    exchange_distribution: Dict[str, Any]
    active_positions: List[str]
    replay_seq_id: int


# Dependencies
def get_runner() -> ProjectionRunner:
    return ProjectionRunner(
        registry=global_registry,
        session_factory=get_session,
    )


@router.post("/rebuild", response_model=WhaleRebuildResponse)
def rebuild_whale_projection(
    runner: ProjectionRunner = Depends(get_runner),
):
    """Clears and fully rebuilds the Whale Materialized View from sequence 1."""
    try:
        metrics = runner.rebuild_projection("WhaleProjection")
        return WhaleRebuildResponse(
            status=metrics["status"],
            events_processed=metrics["events_processed"],
            failed_events=metrics["failed_events"],
            rebuild_duration=metrics["rebuild_duration"],
            replay_speed=metrics["replay_speed"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {e}")


@router.post("/replay")
def replay_whale_projection(
    req: WhaleReplayRequest,
    runner: ProjectionRunner = Depends(get_runner),
):
    """Replays L0 events in a specific sequence ID range to update WhaleView."""
    try:
        res = runner.replay_projection(
            projection_name="WhaleProjection",
            start_seq_id=req.start_seq_id,
            end_seq_id=req.end_seq_id,
        )
        return {
            "status": "SUCCESS",
            "events_processed": res["events_processed"],
            "failed_events": res["failed_events"],
            "last_processed_seq_id": res["last_processed_seq_id"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay failed: {e}")


@router.get("/state", response_model=List[WhaleViewSchema])
def get_whale_state(
    runner: ProjectionRunner = Depends(get_runner),
):
    """Retrieves the full materialized state of all whales currently tracked in WhaleView."""
    session = runner.session_factory()
    try:
        whales = session.query(WhaleView).all()
        return [
            WhaleViewSchema(
                wallet_id=w.wallet_id,
                total_events=w.total_events,
                accumulation_score=w.accumulation_score,
                distribution_score=w.distribution_score,
                realized_accuracy=w.realized_accuracy,
                trust_score=w.trust_score,
                last_activity=w.last_activity.isoformat() if w.last_activity else None,
                exchange_distribution=w.exchange_distribution or {},
                active_positions=w.active_positions or [],
                replay_seq_id=w.replay_seq_id,
            )
            for w in whales
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load whale state: {e}")
    finally:
        session.close()


@router.get("/lookup/{wallet_id}", response_model=WhaleViewSchema)
def lookup_single_wallet(
    wallet_id: str,
    runner: ProjectionRunner = Depends(get_runner),
):
    """Looks up the latest materialized state for a single whale wallet by wallet ID."""
    session = runner.session_factory()
    try:
        w = session.query(WhaleView).filter(WhaleView.wallet_id == wallet_id).first()
        if not w:
            raise HTTPException(status_code=404, detail=f"Whale wallet '{wallet_id}' not found in WhaleView.")
        return WhaleViewSchema(
            wallet_id=w.wallet_id,
            total_events=w.total_events,
            accumulation_score=w.accumulation_score,
            distribution_score=w.distribution_score,
            realized_accuracy=w.realized_accuracy,
            trust_score=w.trust_score,
            last_activity=w.last_activity.isoformat() if w.last_activity else None,
            exchange_distribution=w.exchange_distribution or {},
            active_positions=w.active_positions or [],
            replay_seq_id=w.replay_seq_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to lookup wallet '{wallet_id}': {e}")
    finally:
        session.close()


@router.get("/statistics", response_model=Dict[str, Any])
def get_whale_projection_statistics(
    runner: ProjectionRunner = Depends(get_runner),
):
    """Returns database and processing statistics specifically for the Whale projection."""
    session = runner.session_factory()
    try:
        total_whales = session.query(WhaleView).count()
        proj = runner.registry.get_by_name("WhaleProjection")
        health_stats = proj.health() if proj else {}

        return {
            "total_materialized_whales": total_whales,
            "processed_events": health_stats.get("processed_events", 0),
            "updated_whales": health_stats.get("updated_whales", 0),
            "ignored_events": health_stats.get("ignored_events", 0),
            "failed_updates": health_stats.get("failed_updates", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read statistics: {e}")
    finally:
        session.close()


@router.get("/health", response_model=Dict[str, Any])
def get_whale_projection_health(
    runner: ProjectionRunner = Depends(get_runner),
):
    """Returns the custom diagnostics health status for WhaleProjection."""
    session = runner.session_factory()
    try:
        proj = runner.registry.get_by_name("WhaleProjection")
        if not proj:
            raise HTTPException(status_code=404, detail="WhaleProjection is not registered.")

        state = session.query(ProjectionState).filter(ProjectionState.projection_name == "WhaleProjection").first()
        diagnostics = proj.health()

        return {
            "projection_name": "WhaleProjection",
            "healthy": (state.health_status == "HEALTHY") if state else True,
            "status": state.health_status if state else "HEALTHY",
            "last_processed_seq_id": state.last_processed_seq_id if state else 0,
            "last_error": state.last_error if state else None,
            "diagnostics": diagnostics,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch health check: {e}")
    finally:
        session.close()
