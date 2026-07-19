import logging

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    JSON,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

from config import DATABASE_URL

logger = logging.getLogger(__name__)

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=not _is_sqlite,
    pool_size=1 if _is_sqlite else 10,
    max_overflow=0 if _is_sqlite else 20,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

# ------------------------------------------------------------------
# SIGNAL TABLE
# ------------------------------------------------------------------

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10))
    timeframe = Column(String(10))
    divergence = Column(String(50))

    price = Column(Float)

    score = Column(Float, default=0)
    confidence = Column(Float, default=0)

    market_health = Column(Float, default=0)
    btc_health = Column(Float, default=0)

    volume_score = Column(Float, default=0)
    funding_score = Column(Float, default=0)
    oi_score = Column(Float, default=0)
    cvd_score = Column(Float, default=0)
    trend_score = Column(Float, default=0)
    risk_score = Column(Float, default=0)

    approved = Column(Boolean, default=False)

    status = Column(String(30), default="OPEN")

    reason = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

# ------------------------------------------------------------------
# TRADE TABLE
# ------------------------------------------------------------------

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)

    signal_id = Column(Integer)

    symbol = Column(String(20))
    side = Column(String(10))

    entry = Column(Float)
    stop = Column(Float)

    tp1 = Column(Float)
    tp2 = Column(Float)

    rr = Column(Float)

    pnl = Column(Float, default=0)

    status = Column(String(30), default="OPEN")

    exit_price = Column(Float)

    closed_at = Column(DateTime(timezone=True))

    close_reason = Column(String(30))

    exchange_order_id = Column(String(120))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ------------------------------------------------------------------
# USER TABLE
# ------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ------------------------------------------------------------------
# USER SETTINGS TABLE
# ------------------------------------------------------------------

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    timezone = Column(String(50), default="UTC")
    dashboard_config = Column(JSON, default=dict)
    risk_preferences = Column(JSON, default=dict)
    theme = Column(String(20), default="dark")
    layout_config = Column(JSON, default=dict)
    notification_preferences = Column(JSON, default=dict)


# ------------------------------------------------------------------
# NOTIFICATION TABLE
# ------------------------------------------------------------------

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String(30), nullable=False, index=True)
    payload = Column(JSON, default=dict)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ------------------------------------------------------------------
# WATCHLIST TABLE
# ------------------------------------------------------------------

class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    name = Column(String(50), nullable=False, default="Default")
    symbols = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ------------------------------------------------------------------
# JOURNAL ENTRY TABLE
# ------------------------------------------------------------------

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String(20), index=True)
    side = Column(String(10))
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)

    score = Column(Float, default=0)
    confidence = Column(Float, default=0)

    entry_reason = Column(Text)
    exit_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    result = Column(String(20), default="PENDING")
    pnl = Column(Float, default=0)

    signal_id = Column(Integer, nullable=True)
    trade_id = Column(Integer, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ------------------------------------------------------------------
# PAPER ORDER TABLE
# ------------------------------------------------------------------

class PaperOrder(Base):
    __tablename__ = "paper_orders"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), default="MARKET")
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    filled_price = Column(Float, nullable=True)
    filled_quantity = Column(Float, nullable=True)
    status = Column(String(20), default="PENDING")
    trade_id = Column(Integer, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ------------------------------------------------------------------
# PAPER TRADE TABLE
# ------------------------------------------------------------------

class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, nullable=False)
    order_id = Column(Integer, nullable=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    entry = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    pnl = Column(Float, default=0)
    status = Column(String(20), default="OPEN")
    close_reason = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)


# ------------------------------------------------------------------
# DECISION EXPLANATION TABLE
# ------------------------------------------------------------------


class DecisionExplanation(Base):
    __tablename__ = "decision_explanations"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)

    decision = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)

    reasons = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    supporting_signals = Column(JSON, default=list)
    risk_notes = Column(JSON, default=list)

    summary = Column(Text, default="")

    technical_score = Column(Float, default=0.0)
    whale_score = Column(Float, default=0.0)
    news_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)

    portfolio_total_equity = Column(Float, default=0.0)
    portfolio_unrealized_pnl = Column(Float, default=0.0)
    portfolio_realized_pnl = Column(Float, default=0.0)
    portfolio_exposure = Column(Float, default=0.0)

    performance_sharpe = Column(Float, default=0.0)
    performance_sortino = Column(Float, default=0.0)
    performance_calmar = Column(Float, default=0.0)
    performance_profit_factor = Column(Float, default=0.0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ------------------------------------------------------------------
# SIMULATION SESSION TABLE
# ------------------------------------------------------------------

class SimulationSession(Base):
    __tablename__ = "simulation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    scenario_name = Column(String(50), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    current_index = Column(Integer, default=0)
    mode = Column(String(30), default="MANUAL")
    initial_balance = Column(Float, default=100000.0)
    current_balance = Column(Float, default=100000.0)
    metrics = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ------------------------------------------------------------------
# SIMULATION TRADE TABLE
# ------------------------------------------------------------------

class SimulationTrade(Base):
    __tablename__ = "simulation_trades"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    leverage = Column(Float, default=1.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    pnl = Column(Float, default=0.0)
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, CANCEL
    close_reason = Column(String(30), nullable=True)  # TP_HIT, SL_HIT, MANUAL, REVERSED
    elite_score = Column(Float, default=0.0)
    explain_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)


# ------------------------------------------------------------------
# TRADE STATUS CONSTANTS
# ------------------------------------------------------------------

OPEN = "OPEN"
CLOSE = "CLOSE"
TAKE_PROFIT = "TAKE_PROFIT"
STOP_LOSS = "STOP_LOSS"
CANCEL = "CANCEL"
TP_HIT = "TP_HIT"
SL_HIT = "SL_HIT"
CLOSED = "CLOSED"
PENDING = "PENDING"
FILLED = "FILLED"
PARTIALLY_FILLED = "PARTIALLY_FILLED"

ORDER_STATUSES = frozenset({PENDING, FILLED, PARTIALLY_FILLED, CANCEL})
TRADE_STATUSES = frozenset({OPEN, TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL})
FINAL_STATUSES = frozenset({TP_HIT, SL_HIT, CLOSED, CANCEL})
ORDER_FINAL_STATUSES = frozenset({FILLED, CANCEL})
TRADE_FINAL_STATUSES = frozenset({TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL})

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def get_session():
    return SessionLocal()


def create_tables():
    Base.metadata.create_all(bind=engine)


# ------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------

if __name__ == "__main__":
    create_tables()
    logger.info("Database initialized successfully.")

from contextlib import contextmanager

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def update_signal_status(signal_id, new_status):
    if signal_id is None:
        logger.warning("update_signal_status called with None signal_id")
        return False

    session = get_session()

    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()

        if not signal:
            logger.warning("Signal %s not found for status update", signal_id)
            return False

        signal.status = new_status
        session.commit()
        logger.debug("Signal %s status updated to %s", signal_id, new_status)
        return True

    except Exception as e:
        session.rollback()
        logger.error("Failed to update signal %s status: %s", signal_id, e)
        return False

    finally:
        session.close()
