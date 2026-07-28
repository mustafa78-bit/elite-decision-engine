import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from memory.l2_graph.registry import NodeRegistry, EdgeRegistry
from memory.l2_graph.models import GraphEdge

logger = logging.getLogger(__name__)


class RelationshipBuilder:
    """Fluent builder pattern for constructing and persisting directed relationships (edges)

    between Layer 2 GraphNodes with complete provenance tracking and evidence integration.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._source_type: Optional[str] = None
        self._source_id: Optional[str] = None
        self._source_props: Dict[str, Any] = {}

        self._target_type: Optional[str] = None
        self._target_id: Optional[str] = None
        self._target_props: Dict[str, Any] = {}

        self._rel_type: Optional[str] = None
        self._confidence: float = 1.0
        self._provenance: Dict[str, Any] = {}
        self._supporting_event_ids: List[str] = []
        self._supporting_projection_ids: List[str] = []
        self._created_seq_id: int = 0

    def source(self, node_type: str, external_id: str, properties: Optional[Dict[str, Any]] = None) -> "RelationshipBuilder":
        """Sets the source node for this relationship."""
        self._source_type = node_type
        self._source_id = str(external_id)
        self._source_props = properties or {}
        return self

    def target(self, node_type: str, external_id: str, properties: Optional[Dict[str, Any]] = None) -> "RelationshipBuilder":
        """Sets the target node for this relationship."""
        self._target_type = node_type
        self._target_id = str(external_id)
        self._target_props = properties or {}
        return self

    def relationship(self, relationship_type: str) -> "RelationshipBuilder":
        """Sets the relationship type (e.g., influenced_by, traded, mentions)."""
        self._rel_type = relationship_type
        return self

    def evidence(
        self,
        confidence: float = 1.0,
        provenance: Optional[Dict[str, Any]] = None,
        supporting_event_ids: Optional[List[str]] = None,
        supporting_projection_ids: Optional[List[str]] = None,
        created_seq_id: int = 0,
    ) -> "RelationshipBuilder":
        """Configures confidence, provenance, and supporting IDs representing evidence for the relationship."""
        self._confidence = confidence
        self._provenance = provenance or {}
        self._supporting_event_ids = supporting_event_ids or []
        self._supporting_projection_ids = supporting_projection_ids or []
        self._created_seq_id = created_seq_id
        return self

    def commit(self) -> GraphEdge:
        """Saves and commits the nodes and relationship edge to the database, returning the resulting GraphEdge."""
        if not self._source_type or not self._source_id:
            raise ValueError("Source node type and external_id are required.")
        if not self._target_type or not self._target_id:
            raise ValueError("Target node type and external_id are required.")
        if not self._rel_type:
            raise ValueError("Relationship type is required.")

        # 1. Retrieve or create source node
        source_node = NodeRegistry.get_or_create_node(
            self.session,
            node_type=self._source_type,
            external_id=self._source_id,
            properties=self._source_props,
        )

        # 2. Retrieve or create target node
        target_node = NodeRegistry.get_or_create_node(
            self.session,
            node_type=self._target_type,
            external_id=self._target_id,
            properties=self._target_props,
        )

        # 3. Retrieve, create or update edge monotonically with evidence validation
        edge = EdgeRegistry.get_or_create_edge(
            self.session,
            source_node_id=source_node.id,
            target_node_id=target_node.id,
            relationship_type=self._rel_type,
            confidence=self._confidence,
            provenance=self._provenance,
            supporting_event_ids=self._supporting_event_ids,
            supporting_projection_ids=self._supporting_projection_ids,
            created_seq_id=self._created_seq_id,
        )

        return edge
