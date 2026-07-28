from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from database import get_session
from memory.l1_views.base import BaseProjection
from memory.l1_views.registry import ProjectionRegistry, global_registry
from memory.l1_views.runner import ProjectionRunner, ReplayCursor
from memory.l1_views.models import ProjectionState

router = APIRouter(prefix="/nexus/l1", tags=["NEXUS L1 Projection Framework"])


# Pydantic Schemas
class ReplayRequest(BaseModel):
    start_seq_id: int = Field(..., ge=1, description="Sequence ID to start replaying from")
    end_seq_id: Optional[int] = Field(None, ge=1, description="Sequence ID to stop replaying at")


class ReplayResponse(BaseModel):
    status: str
    events_processed: int
    failed_events: int
    last_processed_seq_id: int


class RebuildResponse(BaseModel):
    status: str
    projection_name: str
    events_processed: int
    failed_events: int
    rebuild_duration: float
    replay_speed: float


class MetricsResponse(BaseModel):
    replay_speed: float
    processed_events: int
    replay_lag: int
    failed_events: int
    retry_count: int
    rebuild_duration: float
    active_projection_count: int


class ProjectionStatusResponse(BaseModel):
    projection_name: str
    last_processed_seq_id: int
    rebuild_status: str
    health_status: str
    last_error: Optional[str] = None
    updated_at: Optional[str] = None


class ProjectionInfo(BaseModel):
    name: str
    supported_events: List[str]


# Dependencies
def get_runner() -> ProjectionRunner:
    return ProjectionRunner(
        registry=global_registry,
        session_factory=get_session,
    )


@router.get("/projections", response_model=List[ProjectionInfo])
def list_projections(
    registry: ProjectionRegistry = Depends(lambda: global_registry),
):
    """Lists all currently registered projections in the L1 framework."""
    try:
        return [
            ProjectionInfo(
                name=p.projection_name,
                supported_events=p.supported_event_types(),
            )
            for p in registry.list_projections()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list projections: {e}")


@router.get("/status/{projection_name}", response_model=ProjectionStatusResponse)
def get_projection_status(
    projection_name: str,
    runner: ProjectionRunner = Depends(get_runner),
):
    """Retrieves the database checkpoint status and progress of a single projection."""
    session = runner.session_factory()
    try:
        # Check if the projection is registered
        if not runner.registry.get_by_name(projection_name):
            raise HTTPException(status_code=404, detail=f"Projection '{projection_name}' is not registered.")

        state = session.query(ProjectionState).filter(ProjectionState.projection_name == projection_name).first()
        if not state:
            return ProjectionStatusResponse(
                projection_name=projection_name,
                last_processed_seq_id=0,
                rebuild_status="IDLE",
                health_status="HEALTHY",
            )

        return ProjectionStatusResponse(
            projection_name=state.projection_name,
            last_processed_seq_id=state.last_processed_seq_id,
            rebuild_status=state.rebuild_status,
            health_status=state.health_status,
            last_error=state.last_error,
            updated_at=state.updated_at.isoformat() if state.updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch status: {e}")
    finally:
        session.close()


@router.post("/rebuild/{projection_name}", response_model=RebuildResponse)
def rebuild_projection(
    projection_name: str,
    runner: ProjectionRunner = Depends(get_runner),
):
    """Triggers a clean full rebuild of a single projection from scratch (Seq 1)."""
    try:
        if not runner.registry.get_by_name(projection_name):
            raise HTTPException(status_code=404, detail=f"Projection '{projection_name}' is not registered.")

        metrics = runner.rebuild_projection(projection_name)
        return RebuildResponse(
            status=metrics["status"],
            projection_name=metrics["projection_name"],
            events_processed=metrics["events_processed"],
            failed_events=metrics["failed_events"],
            rebuild_duration=metrics["rebuild_duration"],
            replay_speed=metrics["replay_speed"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {e}")


@router.post("/replay/{projection_name}", response_model=ReplayResponse)
def replay_projection(
    projection_name: str,
    req: ReplayRequest,
    runner: ProjectionRunner = Depends(get_runner),
):
    """Triggers a manual sequential replay range of events for a single projection."""
    try:
        if not runner.registry.get_by_name(projection_name):
            raise HTTPException(status_code=404, detail=f"Projection '{projection_name}' is not registered.")

        res = runner.replay_projection(
            projection_name=projection_name,
            start_seq_id=req.start_seq_id,
            end_seq_id=req.end_seq_id,
        )
        return ReplayResponse(
            status="SUCCESS",
            events_processed=res["events_processed"],
            failed_events=res["failed_events"],
            last_processed_seq_id=res["last_processed_seq_id"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay failed: {e}")


@router.get("/metrics", response_model=MetricsResponse)
def get_projection_metrics(
    runner: ProjectionRunner = Depends(get_runner),
):
    """Exposes aggregate framework performance, lag, speed, and execution metrics."""
    try:
        m = runner.get_metrics()
        return MetricsResponse(
            replay_speed=m["replay_speed"],
            processed_events=m["processed_events"],
            replay_lag=m["replay_lag"],
            failed_events=m["failed_events"],
            retry_count=m["retry_count"],
            rebuild_duration=m["rebuild_duration"],
            active_projection_count=m["active_projection_count"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load metrics: {e}")


@router.get("/health/{projection_name}", response_model=Dict[str, Any])
def get_projection_health(
    projection_name: str,
    runner: ProjectionRunner = Depends(get_runner),
):
    """Returns detailed diagnostics health and error metadata of a single projection."""
    session = runner.session_factory()
    try:
        projection = runner.registry.get_by_name(projection_name)
        if not projection:
            raise HTTPException(status_code=404, detail=f"Projection '{projection_name}' is not registered.")

        state = session.query(ProjectionState).filter(ProjectionState.projection_name == projection_name).first()

        # Merge framework checkpoint details with projection custom diagnostics
        diagnostics = projection.health()

        return {
            "projection_name": projection_name,
            "status": state.health_status if state else "HEALTHY",
            "healthy": (state.health_status == "HEALTHY") if state else True,
            "last_processed_seq_id": state.last_processed_seq_id if state else 0,
            "rebuild_status": state.rebuild_status if state else "IDLE",
            "last_error": state.last_error if state else None,
            "diagnostics": diagnostics,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")
    finally:
        session.close()


@router.post("/register-mock", response_model=Dict[str, Any])
def register_mock_projection(
    name: str = Query(..., description="Name of the mock projection to register"),
    event_types: List[str] = Query(..., description="Event types to subscribe to"),
):
    """Framework API to dynamically register a mock projection for plugin testing/verification."""
    try:
        class MockProjection(BaseProjection):
            @property
            def projection_name(self) -> str:
                return name

            def supported_event_types(self) -> List[str]:
                return event_types

            def apply(self, event) -> None:
                pass

            def rebuild(self) -> None:
                pass

            def snapshot(self) -> Dict[str, Any]:
                return {}

            def restore_snapshot(self, state) -> None:
                pass

            def validate(self) -> bool:
                return True

            def health(self) -> Dict[str, Any]:
                return {"mock": True}

        proj = MockProjection()
        global_registry.register(proj)
        return {"status": "SUCCESS", "registered_name": name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
