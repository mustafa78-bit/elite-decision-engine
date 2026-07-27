from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from memory.l0_event_log.service import L0EventStore

router = APIRouter(prefix="/nexus/memory", tags=["NEXUS Memory"])


# Pydantic Schemas
class ActorSchema(BaseModel):
    id: str
    type: str = "SYSTEM"
    name: str


class AppendEventRequest(BaseModel):
    event_type: str = Field(..., description="Canonical event type")
    payload: Dict[str, Any] = Field(..., description="Dynamic payload dictionary")
    actor: ActorSchema
    causal_chain_id: str
    parent_event_id: Optional[str] = None
    sources: Optional[List[str]] = None
    version: str = "1.0.0"


class AppendBatchRequest(BaseModel):
    events: List[AppendEventRequest]


class SnapshotRequest(BaseModel):
    causal_chain_id: str
    last_seq_id: int
    state: Dict[str, Any]


# Route Implementations
@router.post("/events", response_model=Dict[str, Any])
def append_event(
    req: AppendEventRequest,
    store: L0EventStore = Depends(L0EventStore),
):
    """Appends a single immutable event to the L0 Event Log."""
    try:
        event = store.append(
            event_type=req.event_type,
            payload=req.payload,
            actor=req.actor.dict(),
            causal_chain_id=req.causal_chain_id,
            parent_event_id=req.parent_event_id,
            sources=req.sources,
            version=req.version,
        )
        return {
            "status": "success",
            "event_id": event.event_id,
            "seq_id": event.seq_id,
            "checksum": event.checksum,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to append event: {e}")


@router.post("/events/batch", response_model=Dict[str, Any])
def append_batch(
    req: AppendBatchRequest,
    store: L0EventStore = Depends(L0EventStore),
):
    """Appends a batch of immutable events to the L0 Event Log."""
    try:
        events_data = []
        for e in req.events:
            events_data.append({
                "event_type": e.event_type,
                "payload": e.payload,
                "actor": e.actor.dict(),
                "causal_chain_id": e.causal_chain_id,
                "parent_event_id": e.parent_event_id,
                "sources": e.sources,
                "version": e.version,
            })
        persisted = store.append_batch(events_data)
        return {
            "status": "success",
            "processed_count": len(persisted),
            "events": [
                {
                    "event_id": evt.event_id,
                    "seq_id": evt.seq_id,
                    "checksum": evt.checksum,
                }
                for evt in persisted
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to append batch: {e}")


@router.get("/events", response_model=Dict[str, Any])
def read_events(
    start_seq_id: Optional[int] = Query(None, ge=1),
    end_seq_id: Optional[int] = Query(None, ge=1),
    causal_chain_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    include_quarantined: bool = False,
    store: L0EventStore = Depends(L0EventStore),
):
    """Retrieves list of filtered immutable events from L0 Event Log."""
    try:
        events = store.read_events(
            start_seq_id=start_seq_id,
            end_seq_id=end_seq_id,
            causal_chain_id=causal_chain_id,
            event_type=event_type,
            limit=limit,
            offset=offset,
            include_quarantined=include_quarantined,
        )
        return {
            "status": "success",
            "count": len(events),
            "events": [
                {
                    "event_id": e.event_id,
                    "seq_id": e.seq_id,
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "version": e.version,
                    "actor": {
                        "id": e.actor_id,
                        "type": e.actor_type,
                        "name": e.actor_name,
                    },
                    "provenance": {
                        "parent_event_id": e.parent_event_id,
                        "causal_chain_id": e.causal_chain_id,
                        "sources": e.sources,
                    },
                    "payload": e.payload,
                    "checksum": e.checksum,
                    "is_quarantined": e.is_quarantined,
                }
                for e in events
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query events: {e}")


@router.get("/provenance/{causal_chain_id}", response_model=Dict[str, Any])
def get_provenance_chain(
    causal_chain_id: str,
    store: L0EventStore = Depends(L0EventStore),
):
    """Reconstructs the full historical provenance chain (causal DAG) sequentially."""
    try:
        events = store.read_events(causal_chain_id=causal_chain_id, limit=500)
        # Order sequentially to form lineage
        nodes = []
        edges = []
        for e in events:
            nodes.append({
                "id": e.event_id,
                "type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
            })
            if e.parent_event_id:
                edges.append({
                    "source": e.parent_event_id,
                    "target": e.event_id,
                    "relation": "caused_by",
                })

        return {
            "causal_chain_id": causal_chain_id,
            "nodes": nodes,
            "edges": edges,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate provenance DAG: {e}")


@router.post("/verify", response_model=Dict[str, Any])
def verify_ledger(
    store: L0EventStore = Depends(L0EventStore),
):
    """Executes a full-integrity SHA-256 validation scan over L0 log to isolate corruptions."""
    try:
        corrupted, quarantined = store.verify_integrity()
        return {
            "status": "success" if not corrupted else "tampered_events_isolated",
            "is_healthy": len(corrupted) == 0,
            "corrupted_count": len(corrupted),
            "corrupted_event_ids": corrupted,
            "quarantined_event_ids": quarantined,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ledger integrity scan failed: {e}")


@router.post("/snapshot", response_model=Dict[str, Any])
def create_state_snapshot(
    req: SnapshotRequest,
    store: L0EventStore = Depends(L0EventStore),
):
    """Saves a materialized state snapshot to optimize future stream replays."""
    try:
        snapshot = store.create_snapshot(
            causal_chain_id=req.causal_chain_id,
            last_seq_id=req.last_seq_id,
            state=req.state,
        )
        return {
            "status": "success",
            "snapshot_id": snapshot.snapshot_id,
            "causal_chain_id": snapshot.causal_chain_id,
            "last_seq_id": snapshot.last_seq_id,
            "checksum": snapshot.checksum,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Snapshot creation failed: {e}")


@router.get("/snapshot/{causal_chain_id}", response_model=Dict[str, Any])
def get_latest_snapshot(
    causal_chain_id: str,
    store: L0EventStore = Depends(L0EventStore),
):
    """Retrieves the latest state snapshot for a causal chain, if any."""
    try:
        snapshot = store.get_latest_snapshot(causal_chain_id=causal_chain_id)
        if not snapshot:
            raise HTTPException(status_code=404, detail="No snapshot found for this chain")
        return {
            "snapshot_id": snapshot.snapshot_id,
            "causal_chain_id": snapshot.causal_chain_id,
            "last_seq_id": snapshot.last_seq_id,
            "timestamp": snapshot.timestamp.isoformat(),
            "state": snapshot.state,
            "checksum": snapshot.checksum,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read snapshot: {e}")
