import logging
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    JSON,
)
from sqlalchemy.sql import func
from database import Base

logger = logging.getLogger(__name__)


class ExperienceSubstrate(Base):
    """The raw, chronological, walk-forward substrate of lived platform experiences."""

    __tablename__ = "experience_substrates"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)

    # Features/Indicators snapshot at the timestamp (e.g. trend_score, volume_score, rsi, regime)
    state_snapshot = Column(JSON, nullable=False, default=dict)

    # Action taken (e.g. LONG, SHORT, REJECT)
    action_taken = Column(String(30), nullable=False)

    # Outcome realized (e.g. realized PnL of the resulting trade)
    outcome = Column(Float, nullable=True)
    realized_at = Column(DateTime(timezone=True), nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class InstinctState(Base):
    """The stateful, synthesized instinct profiles representing behavioral dispositions.

    Tracks incremental statistics to support real-time stateful evolution without expensive database scans.
    """

    __tablename__ = "instinct_states"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)

    # Instinct must represent a continuously evolving behavioral disposition.
    # It stores parameters like: courage, defensiveness, conviction, and adaptability.
    disposition_vector = Column(JSON, nullable=False, default=dict)

    # Evolving status metrics contributing to instinct, but not becoming instinct itself
    win_rate = Column(Float, default=0.0)
    profit_factor = Column(Float, default=1.0)
    total_trades = Column(Integer, default=0)
    avg_pnl = Column(Float, default=0.0)
    vibe_score = Column(Float, default=0.0)

    # Stateful fields to support true mathematical incremental updates without DB scans
    gross_wins = Column(Float, default=0.0)
    gross_losses = Column(Float, default=0.0)
    win_count = Column(Integer, default=0)
    loss_count = Column(Integer, default=0)
    cumulative_pnl = Column(Float, default=0.0)

    # Store list of recent outcomes to update vibe score incrementally
    recent_outcomes = Column(JSON, nullable=False, default=list)

    # Tracking chronological bounds (Exposure check)
    first_experience_time = Column(DateTime(timezone=True), nullable=True)
    last_experience_time = Column(DateTime(timezone=True), nullable=True)
    unique_regimes_encountered = Column(JSON, nullable=False, default=list)

    last_updated = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ExperienceGraduation(Base):
    """Governance boundaries determining if an environment has graduated from raw instinct.

    Graduation must never self-promote. Only explicit Governance approval activates graduation.
    """

    __tablename__ = "experience_graduations"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)

    # Graduation Status (e.g. 'PENDING', 'RECOMMENDED', 'APPROVED_BY_GOVERNANCE', 'REJECTED_BY_GOVERNANCE')
    status = Column(String(40), default="PENDING", nullable=False, index=True)

    # Active graduated state (True ONLY when status is 'APPROVED_BY_GOVERNANCE')
    graduated = Column(Boolean, default=False, index=True)
    recommended_at = Column(DateTime(timezone=True), nullable=True)
    graduated_at = Column(DateTime(timezone=True), nullable=True)

    # Proposed and final governance bounds
    recommendation_payload = Column(JSON, nullable=False, default=dict)
    governance_rules = Column(JSON, nullable=False, default=dict)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
