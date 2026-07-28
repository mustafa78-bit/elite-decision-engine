from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class GraphNode(Base):
    """SQLAlchemy model representing a node in the Layer 2 Knowledge/Relationship Graph."""

    __tablename__ = "l2_graph_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_type = Column(String(50), nullable=False, index=True)  # Coin, Whale, News, Decision, Portfolio, Strategy, Indicator, Market Regime
    external_id = Column(String(100), nullable=False, index=True)  # symbol, wallet_address, decision_id, news_id, etc.
    properties = Column(JSON, default=dict, nullable=False)  # arbitrary metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("node_type", "external_id", name="uq_node_type_external_id"),
    )

    def to_dict(self):
        """Serializes the node object to a dict."""
        return {
            "id": self.id,
            "node_type": self.node_type,
            "external_id": self.external_id,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class GraphEdge(Base):
    """SQLAlchemy model representing a directed edge (relationship) between two nodes with evidence and provenance."""

    __tablename__ = "l2_graph_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("l2_graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_node_id = Column(Integer, ForeignKey("l2_graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, index=True)  # influenced_by, traded, accumulated, distributed, mentions, follows, confirmed_by, contradicted_by, belongs_to, generated

    confidence = Column(Float, default=1.0, nullable=False)
    provenance = Column(JSON, default=dict, nullable=False)  # tracking metadata (e.g. causal chain, system details)
    supporting_event_ids = Column(JSON, default=list, nullable=False)  # list of source L0 event_ids
    supporting_projection_ids = Column(JSON, default=list, nullable=False)  # list of source L1 projection view names or IDs
    created_seq_id = Column(Integer, default=0, nullable=False)  # L0 seq_id of the event that created/updated this relationship
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships for easier traversal
    source_node = relationship("GraphNode", foreign_keys=[source_node_id], backref="outgoing_edges")
    target_node = relationship("GraphNode", foreign_keys=[target_node_id], backref="incoming_edges")

    __table_args__ = (
        UniqueConstraint("source_node_id", "target_node_id", "relationship_type", name="uq_edge_source_target_rel"),
    )

    def to_dict(self):
        """Serializes the edge object to a dict."""
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "relationship_type": self.relationship_type,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "supporting_event_ids": self.supporting_event_ids,
            "supporting_projection_ids": self.supporting_projection_ids,
            "created_seq_id": self.created_seq_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class GraphSnapshot(Base):
    """SQLAlchemy model for storing consistency snapshots of the Layer 2 Relationship Graph."""

    __tablename__ = "l2_graph_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(String(36), unique=True, index=True, nullable=False)
    last_sequence_number = Column(Integer, nullable=False)
    nodes_data = Column(JSON, nullable=False)  # list of serialized nodes
    edges_data = Column(JSON, nullable=False)  # list of serialized edges
    integrity_hash = Column(String(64), nullable=False)  # SHA-256 integrity signature of snapshot content
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        """Serializes the snapshot object to a dict."""
        return {
            "id": self.id,
            "snapshot_id": self.snapshot_id,
            "last_sequence_number": self.last_sequence_number,
            "integrity_hash": self.integrity_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
