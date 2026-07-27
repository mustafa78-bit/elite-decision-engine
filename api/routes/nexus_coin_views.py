import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from database import get_session
from memory.l1_views.registry import global_registry
from memory.l1_views.runner import ProjectionRunner, ReplayCursor
from memory.l1_views.models import CoinView, ProjectionState

router = APIRouter(prefix="/nexus/l1/coin", tags=["NEXUS Coin Materialized View"])


# Pydantic Schemas
class CoinReplayRequest(BaseModel):
    start_seq_id: int = Field(..., ge=1, description="Sequence ID to start replaying from")
    end_seq_id: Optional[int] = Field(None, ge=1, description="Sequence ID to stop replaying at")


class CoinRebuildResponse(BaseModel):
    status: str
    events_processed: int
    failed_events: int
    rebuild_duration: float
    replay_speed: float


class CoinViewSchema(BaseModel):
    coin_id: str
    symbol: str
    latest_price: float
    last_price_timestamp: Optional[str] = None
    market_regime: str
    trust_score: float
    confidence_score: float
    latest_news_id: Optional[str] = None
    latest_news_timestamp: Optional[str] = None
    latest_whale_activity: Dict[str, Any]
    active_patterns: List[str]
    calibration_version: str
    trust_version: str
    replay_seq_id: int


# Dependencies
def get_runner() -> ProjectionRunner:
    return ProjectionRunner(
        registry=global_registry,
        session_factory=get_session,
    )


@router.post("/rebuild", response_model=CoinRebuildResponse)
def rebuild_coin_projection(
    runner: ProjectionRunner = Depends(get_runner),
):
    """Clears and fully rebuilds the Coin Materialized View from sequence 1."""
    try:
        metrics = runner.rebuild_projection("CoinProjection")
        return CoinRebuildResponse(
            status=metrics["status"],
            events_processed=metrics["events_processed"],
            failed_events=metrics["failed_events"],
            rebuild_duration=metrics["rebuild_duration"],
            replay_speed=metrics["replay_speed"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {e}")


@router.post("/replay")
def replay_coin_projection(
    req: CoinReplayRequest,
    runner: ProjectionRunner = Depends(get_runner),
):
    """Replays L0 events in a specific sequence ID range to update CoinView."""
    try:
        res = runner.replay_projection(
            projection_name="CoinProjection",
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


@router.get("/state", response_model=List[CoinViewSchema])
def get_coin_state(
    runner: ProjectionRunner = Depends(get_runner),
):
    """Retrieves the full materialized state of all coins currently tracked in CoinView."""
    session = runner.session_factory()
    try:
        coins = session.query(CoinView).all()
        return [
            CoinViewSchema(
                coin_id=c.coin_id,
                symbol=c.symbol,
                latest_price=c.latest_price,
                last_price_timestamp=c.last_price_timestamp.isoformat() if c.last_price_timestamp else None,
                market_regime=c.market_regime,
                trust_score=c.trust_score,
                confidence_score=c.confidence_score,
                latest_news_id=c.latest_news_id,
                latest_news_timestamp=c.latest_news_timestamp.isoformat() if c.latest_news_timestamp else None,
                latest_whale_activity=c.latest_whale_activity or {},
                active_patterns=c.active_patterns or [],
                calibration_version=c.calibration_version,
                trust_version=c.trust_version,
                replay_seq_id=c.replay_seq_id,
            )
            for c in coins
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load coin state: {e}")
    finally:
        session.close()


@router.get("/lookup/{symbol}", response_model=CoinViewSchema)
def lookup_single_asset(
    symbol: str,
    runner: ProjectionRunner = Depends(get_runner),
):
    """Looks up the latest materialized state for a single coin by its trading symbol (e.g. BTC)."""
    session = runner.session_factory()
    try:
        c = session.query(CoinView).filter(CoinView.symbol == symbol.upper()).first()
        if not c:
            raise HTTPException(status_code=404, detail=f"Asset symbol '{symbol}' not found in CoinView.")
        return CoinViewSchema(
            coin_id=c.coin_id,
            symbol=c.symbol,
            latest_price=c.latest_price,
            last_price_timestamp=c.last_price_timestamp.isoformat() if c.last_price_timestamp else None,
            market_regime=c.market_regime,
            trust_score=c.trust_score,
            confidence_score=c.confidence_score,
            latest_news_id=c.latest_news_id,
            latest_news_timestamp=c.latest_news_timestamp.isoformat() if c.latest_news_timestamp else None,
            latest_whale_activity=c.latest_whale_activity or {},
            active_patterns=c.active_patterns or [],
            calibration_version=c.calibration_version,
            trust_version=c.trust_version,
            replay_seq_id=c.replay_seq_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to lookup asset '{symbol}': {e}")
    finally:
        session.close()


@router.get("/statistics", response_model=Dict[str, Any])
def get_coin_projection_statistics(
    runner: ProjectionRunner = Depends(get_runner),
):
    """Returns database and processing statistics specifically for the Coin projection."""
    session = runner.session_factory()
    try:
        total_coins = session.query(CoinView).count()
        proj = runner.registry.get_by_name("CoinProjection")
        health_stats = proj.health() if proj else {}

        return {
            "total_materialized_coins": total_coins,
            "processed_events": health_stats.get("processed_events", 0),
            "updated_coins": health_stats.get("updated_coins", 0),
            "ignored_events": health_stats.get("ignored_events", 0),
            "failed_updates": health_stats.get("failed_updates", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read statistics: {e}")
    finally:
        session.close()


@router.get("/health", response_model=Dict[str, Any])
def get_coin_projection_health(
    runner: ProjectionRunner = Depends(get_runner),
):
    """Returns the custom diagnostics health status for CoinProjection."""
    session = runner.session_factory()
    try:
        proj = runner.registry.get_by_name("CoinProjection")
        if not proj:
            raise HTTPException(status_code=404, detail="CoinProjection is not registered.")

        state = session.query(ProjectionState).filter(ProjectionState.projection_name == "CoinProjection").first()
        diagnostics = proj.health()

        return {
            "projection_name": "CoinProjection",
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
