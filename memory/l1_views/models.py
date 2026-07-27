from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from database import Base


class ProjectionState(Base):
    """SQLAlchemy model for persisting the sequence ID, checkpoint, and state of registered projections."""

    __tablename__ = "l1_projection_states"

    projection_name = Column(String(100), primary_key=True, index=True)
    last_processed_seq_id = Column(Integer, default=0, nullable=False)
    replay_cursor = Column(JSON, default=dict)
    snapshot_version = Column(String(50), nullable=True)
    snapshot_timestamp = Column(DateTime(timezone=True), nullable=True)
    rebuild_status = Column(String(30), default="IDLE", nullable=False)  # IDLE, RUNNING, COMPLETED, FAILED
    health_status = Column(String(30), default="HEALTHY", nullable=False)  # HEALTHY, DEGRADED, FAILED
    last_error = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
