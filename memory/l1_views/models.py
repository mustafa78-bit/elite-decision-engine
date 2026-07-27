from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text
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


class CoinView(Base):
    """L1 Materialized View for Assets/Coins."""

    __tablename__ = "l1_coin_views"

    coin_id = Column(String(36), primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    latest_price = Column(Float, default=0.0)
    last_price_timestamp = Column(DateTime(timezone=True), nullable=True)
    market_regime = Column(String(50), default="UNKNOWN")
    trust_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    latest_news_id = Column(String(36), nullable=True)
    latest_news_timestamp = Column(DateTime(timezone=True), nullable=True)
    latest_whale_activity = Column(JSON, default=dict)
    active_patterns = Column(JSON, default=list)
    calibration_version = Column(String(20), default="1.0.0")
    trust_version = Column(String(20), default="1.0.0")
    replay_seq_id = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class WhaleView(Base):
    """L1 Materialized View for Tracked Wallets."""

    __tablename__ = "l1_whale_views"

    wallet_id = Column(String(100), primary_key=True, index=True)
    total_events = Column(Integer, default=0)
    accumulation_score = Column(Float, default=0.0)
    distribution_score = Column(Float, default=0.0)
    realized_accuracy = Column(Float, default=0.0)
    trust_score = Column(Float, default=0.0)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    exchange_distribution = Column(JSON, default=dict)
    active_positions = Column(JSON, default=list)
    replay_seq_id = Column(Integer, default=0, nullable=False)


class NewsView(Base):
    """L1 Materialized View for News Intelligence."""

    __tablename__ = "l1_news_views"

    news_id = Column(String(36), primary_key=True, index=True)
    related_assets = Column(JSON, default=list)
    importance = Column(Float, default=0.0)
    sentiment = Column(Float, default=0.0)
    credibility = Column(Float, default=0.0)
    affected_markets = Column(JSON, default=list)
    expiration = Column(DateTime(timezone=True), nullable=True)
    evidence_links = Column(JSON, default=list)
    replay_seq_id = Column(Integer, default=0, nullable=False)


class DecisionView(Base):
    """L1 Materialized View for AI Decisions."""

    __tablename__ = "l1_decision_views"

    decision_id = Column(String(36), primary_key=True, index=True)
    entity = Column(String(100), nullable=False, index=True)
    recommendation = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
    outcome = Column(String(100), nullable=True)
    calibration_version = Column(String(20), default="1.0.0")
    trust_version = Column(String(20), default="1.0.0")
    evidence = Column(JSON, default=dict)
    replay_reference = Column(JSON, default=dict)
    replay_seq_id = Column(Integer, default=0, nullable=False)


class PortfolioView(Base):
    """L1 Materialized View for Portfolio State."""

    __tablename__ = "l1_portfolio_views"

    portfolio_id = Column(String(36), primary_key=True, index=True)
    positions = Column(JSON, default=list)
    exposure = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    allocation = Column(JSON, default=dict)
    drawdown = Column(Float, default=0.0)
    replay_seq_id = Column(Integer, default=0, nullable=False)
