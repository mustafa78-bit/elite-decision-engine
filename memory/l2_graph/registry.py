import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from memory.l2_graph.models import GraphNode, GraphEdge

logger = logging.getLogger(__name__)


class NodeRegistry:
    """Thread-safe, idempotent registry for GraphNode entities."""

    @staticmethod
    def get_node(session: Session, node_type: str, external_id: str) -> Optional[GraphNode]:
        """Retrieves a single GraphNode by its type and external ID."""
        return (
            session.query(GraphNode)
            .filter(GraphNode.node_type == node_type, GraphNode.external_id == external_id)
            .first()
        )

    @staticmethod
    def get_or_create_node(
        session: Session,
        node_type: str,
        external_id: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        """Idempotently retrieves or creates a GraphNode, merging properties monotonically."""
        props = properties or {}
        node = NodeRegistry.get_node(session, node_type, external_id)

        if node:
            # Monotonically merge properties
            current_props = dict(node.properties or {})
            updated = False
            for k, v in props.items():
                if current_props.get(k) != v:
                    current_props[k] = v
                    updated = True
            if updated:
                node.properties = current_props
                session.flush()
            return node

        # Not found, create new node
        try:
            with session.begin_nested():
                node = GraphNode(
                    node_type=node_type,
                    external_id=external_id,
                    properties=props,
                )
                session.add(node)
                session.flush()
            return node
        except IntegrityError:
            session.rollback()
            node = NodeRegistry.get_node(session, node_type, external_id)
            if node:
                current_props = dict(node.properties or {})
                updated = False
                for k, v in props.items():
                    if current_props.get(k) != v:
                        current_props[k] = v
                        updated = True
                if updated:
                    node.properties = current_props
                    session.flush()
                return node
            raise

    @staticmethod
    def list_nodes(session: Session, node_type: Optional[str] = None) -> List[GraphNode]:
        """Lists nodes, optionally filtered by node_type."""
        query = session.query(GraphNode)
        if node_type:
            query = query.filter(GraphNode.node_type == node_type)
        return query.all()


class EdgeRegistry:
    """Thread-safe, idempotent registry for GraphEdge entities.

    Enforces strict monotonic sequence tracking and evidence preservation.
    """

    @staticmethod
    def get_edge(
        session: Session,
        source_node_id: int,
        target_node_id: int,
        relationship_type: str,
    ) -> Optional[GraphEdge]:
        """Retrieves an edge between source and target of the specified relationship type."""
        return (
            session.query(GraphEdge)
            .filter(
                GraphEdge.source_node_id == source_node_id,
                GraphEdge.target_node_id == target_node_id,
                GraphEdge.relationship_type == relationship_type,
            )
            .first()
        )

    @staticmethod
    def get_or_create_edge(
        session: Session,
        source_node_id: int,
        target_node_id: int,
        relationship_type: str,
        confidence: float = 1.0,
        provenance: Optional[Dict[str, Any]] = None,
        supporting_event_ids: Optional[List[str]] = None,
        supporting_projection_ids: Optional[List[str]] = None,
        created_seq_id: int = 0,
    ) -> GraphEdge:
        """Idempotently gets or creates a GraphEdge with strict sequence tracking and evidence.

        Enforces duplicate prevention and evidence trace preservation.
        """
        prov = provenance or {}
        evt_ids = supporting_event_ids or []
        proj_ids = supporting_projection_ids or []

        # Validate that relationship cannot exist without evidence (either an event_id or projection_id)
        if not evt_ids and not proj_ids:
            raise ValueError("Relationships without evidence (supporting events or projections) must never exist.")

        edge = EdgeRegistry.get_edge(session, source_node_id, target_node_id, relationship_type)

        if edge:
            # Monotonic sequence check: ignore out-of-order updates
            if created_seq_id < edge.created_seq_id:
                logger.debug(
                    "Stale update ignored for L2 edge %d due to older sequence_number (%d < %d)",
                    edge.id,
                    created_seq_id,
                    edge.created_seq_id,
                )
                # Keep accumulating evidence even if seq is older
                existing_evts = set(edge.supporting_event_ids or [])
                existing_projs = set(edge.supporting_projection_ids or [])

                updated_evts = list(existing_evts.union(evt_ids))
                updated_projs = list(existing_projs.union(proj_ids))

                if len(updated_evts) != len(existing_evts) or len(updated_projs) != len(existing_projs):
                    edge.supporting_event_ids = sorted(updated_evts)
                    edge.supporting_projection_ids = sorted(updated_projs)
                    session.flush()
                return edge

            # Update fields monotonically and accumulate unique evidence
            existing_evts = set(edge.supporting_event_ids or [])
            existing_projs = set(edge.supporting_projection_ids or [])

            edge.confidence = confidence
            edge.provenance = prov
            edge.supporting_event_ids = sorted(list(existing_evts.union(evt_ids)))
            edge.supporting_projection_ids = sorted(list(existing_projs.union(proj_ids)))
            edge.created_seq_id = created_seq_id
            session.flush()
            return edge

        # Create new edge
        try:
            with session.begin_nested():
                edge = GraphEdge(
                    source_node_id=source_node_id,
                    target_node_id=target_node_id,
                    relationship_type=relationship_type,
                    confidence=confidence,
                    provenance=prov,
                    supporting_event_ids=sorted(list(set(evt_ids))),
                    supporting_projection_ids=sorted(list(set(proj_ids))),
                    created_seq_id=created_seq_id,
                )
                session.add(edge)
                session.flush()
            return edge
        except IntegrityError:
            session.rollback()
            edge = EdgeRegistry.get_edge(session, source_node_id, target_node_id, relationship_type)
            if edge:
                if created_seq_id >= edge.created_seq_id:
                    existing_evts = set(edge.supporting_event_ids or [])
                    existing_projs = set(edge.supporting_projection_ids or [])

                    edge.confidence = confidence
                    edge.provenance = prov
                    edge.supporting_event_ids = sorted(list(existing_evts.union(evt_ids)))
                    edge.supporting_projection_ids = sorted(list(existing_projs.union(proj_ids)))
                    edge.created_seq_id = created_seq_id
                    session.flush()
                return edge
            raise

    @staticmethod
    def list_edges(session: Session, relationship_type: Optional[str] = None) -> List[GraphEdge]:
        """Lists edges, optionally filtered by relationship_type."""
        query = session.query(GraphEdge)
        if relationship_type:
            query = query.filter(GraphEdge.relationship_type == relationship_type)
        return query.all()
