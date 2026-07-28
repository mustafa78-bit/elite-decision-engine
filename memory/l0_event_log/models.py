from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from database import Base


class NEXUSEvent(Base):
    """SQLAlchemy model for L0 Canonical Append-only Event Log."""

    __tablename__ = "nexus_events"

    event_id = Column(String(36), primary_key=True, index=True)
    seq_id = Column(Integer, unique=True, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    version = Column(String(10), default="1.0.0", nullable=False)

    # Actor details
    actor_id = Column(String(100), nullable=False)
    actor_type = Column(String(50), nullable=False)
    actor_name = Column(String(100), nullable=False)

    # Provenance fields
    parent_event_id = Column(String(36), nullable=True, index=True)
    causal_chain_id = Column(String(36), nullable=False, index=True)
    sources = Column(JSON, default=list, nullable=False)

    # Core data & Security signatures
    payload = Column(JSON, nullable=False)
    checksum = Column(String(64), nullable=False)

    # Fault protection / Quarantine mechanism
    is_quarantined = Column(Boolean, default=False, nullable=False)
    quarantine_reason = Column(Text, nullable=True)


class NEXUSSnapshot(Base):
    """SQLAlchemy model for representing materialized state snapshots up to a certain seq_id."""

    __tablename__ = "nexus_snapshots"

    snapshot_id = Column(String(36), primary_key=True, index=True)
    causal_chain_id = Column(String(36), nullable=False, index=True)
    last_seq_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    state = Column(JSON, nullable=False)
    checksum = Column(String(64), nullable=False)
