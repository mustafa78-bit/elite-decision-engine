import logging
import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_session
from memory.l2_graph.engine import GraphEngine
from memory.l2_graph.models import GraphNode, GraphEdge, GraphSnapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["NEXUS L2 Relationship Graph"])


@router.get("/nodes", response_model=List[Dict[str, Any]])
def get_nodes(
    node_type: Optional[str] = Query(None, description="Filter nodes by type (e.g. Coin, Whale)"),
    external_id: Optional[str] = Query(None, description="Filter nodes by external ID"),
    session: Session = Depends(get_session),
):
    """Retrieves all graph nodes with optional filters for node_type and external_id."""
    query = session.query(GraphNode)
    if node_type:
        query = query.filter(GraphNode.node_type == node_type)
    if external_id:
        query = query.filter(GraphNode.external_id == external_id)
    return [node.to_dict() for node in query.all()]


@router.get("/node/{node_id}", response_model=Dict[str, Any])
def get_node(
    node_id: int,
    session: Session = Depends(get_session),
):
    """Retrieves a single GraphNode by its database ID."""
    node = session.query(GraphNode).filter(GraphNode.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with ID {node_id} not found."
        )
    return node.to_dict()


@router.get("/edges", response_model=List[Dict[str, Any]])
def get_edges(
    relationship_type: Optional[str] = Query(None, description="Filter edges by relationship type"),
    source_node_id: Optional[int] = Query(None, description="Filter edges by source node ID"),
    target_node_id: Optional[int] = Query(None, description="Filter edges by target node ID"),
    session: Session = Depends(get_session),
):
    """Retrieves all graph edges with optional filters."""
    query = session.query(GraphEdge)
    if relationship_type:
        query = query.filter(GraphEdge.relationship_type == relationship_type)
    if source_node_id is not None:
        query = query.filter(GraphEdge.source_node_id == source_node_id)
    if target_node_id is not None:
        query = query.filter(GraphEdge.target_node_id == target_node_id)
    return [edge.to_dict() for edge in query.all()]


@router.get("/neighbors/{node_id}", response_model=List[Dict[str, Any]])
def get_neighbors(
    node_id: int,
    session: Session = Depends(get_session),
):
    """Retrieves all directed neighbors and relation steps for the specified node ID."""
    node_exists = session.query(GraphNode.id).filter(GraphNode.id == node_id).first()
    if not node_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with ID {node_id} not found."
        )
    engine = GraphEngine(lambda: session)
    return engine.get_neighbors(node_id)


@router.get("/path", response_model=Optional[List[Dict[str, Any]]])
def get_path(
    start_node_id: int = Query(..., description="The database ID of the starting node"),
    end_node_id: int = Query(..., description="The database ID of the destination node"),
    session: Session = Depends(get_session),
):
    """Finds the shortest directed path between start and end node using Breadth-First Search (BFS)."""
    engine = GraphEngine(lambda: session)
    path = engine.find_shortest_path(start_node_id, end_node_id)
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No path found between node {start_node_id} and node {end_node_id}."
        )
    return path


@router.get("/metrics", response_model=Dict[str, Any])
def get_metrics(session: Session = Depends(get_session)):
    """Retrieves high-density metrics describing graph size, type distribution, and density."""
    engine = GraphEngine(lambda: session)
    return engine.get_metrics()


@router.get("/health", response_model=Dict[str, Any])
def get_health(session: Session = Depends(get_session)):
    """Checks the health of the L2 Relationship Graph, audit for dangling edges, and sync lags."""
    engine = GraphEngine(lambda: session)
    return engine.check_health()


@router.post("/replay", status_code=status.HTTP_200_OK)
def trigger_replay(
    incremental: bool = Query(False, description="If True, only stream events newer than the last processed sequence"),
    session: Session = Depends(get_session),
):
    """Triggers a sequential replay of the L0 Event Log to rebuild the L2 Graph identically."""
    engine = GraphEngine(lambda: session)
    try:
        start_time = time.time()
        if incremental:
            events, edges = engine.replay_incrementally()
            mode = "incremental"
        else:
            events, edges = engine.replay_from_event_store()
            mode = "full"
        duration = time.time() - start_time
        throughput = events / duration if duration > 0 else 0.0

        return {
            "status": "success",
            "message": f"Successfully completed {mode} replay.",
            "events_processed": events,
            "edges_created": edges,
            "replay_duration_seconds": duration,
            "replay_throughput_events_per_second": throughput,
        }
    except Exception as e:
        logger.error("Failed to trigger L2 Graph replay: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Replay failed: {str(e)}",
        )


@router.post("/snapshot", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def trigger_snapshot(session: Session = Depends(get_session)):
    """Creates a cryptographic, SHA-256 verified consistency snapshot of the current graph state."""
    engine = GraphEngine(lambda: session)
    try:
        snapshot = engine.create_snapshot()
        return {
            "status": "success",
            "snapshot_id": snapshot.snapshot_id,
            "last_sequence_number": snapshot.last_sequence_number,
            "integrity_hash": snapshot.integrity_hash,
        }
    except Exception as e:
        logger.error("Failed to create L2 Graph snapshot: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Snapshot creation failed: {str(e)}",
        )


@router.post("/snapshot/restore", status_code=status.HTTP_200_OK)
def trigger_restore(
    snapshot_id: str = Query(..., description="The UUID of the snapshot to restore"),
    session: Session = Depends(get_session),
):
    """Restores the graph state from a consistency snapshot, executing a full cryptographic integrity check."""
    engine = GraphEngine(lambda: session)
    try:
        success = engine.restore_from_snapshot(snapshot_id)
        if success:
            return {
                "status": "success",
                "message": f"Successfully restored L2 Relationship Graph from snapshot {snapshot_id}.",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snapshot {snapshot_id} not found or failed to restore.",
            )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity check failed: {str(val_err)}",
        )
    except Exception as e:
        logger.error("Failed to restore L2 Graph snapshot: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}",
        )
