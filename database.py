import logging
from dotenv import load_dotenv
import os

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# ENV LOAD
# ------------------------------------------------------------------

load_dotenv()

# ------------------------------------------------------------------
# DATABASE CONFIG
# ------------------------------------------------------------------

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "decision_engine")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
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
    client_order_id = Column(String(120))
    exchange_status = Column(String(30), default="NEW")
    submitted_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    filled_at = Column(DateTime(timezone=True))
    average_fill_price = Column(Float)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
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

def update_signal_status(signal_id, new_status):
    session = get_session()

    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()

        if not signal:
            return False

        signal.status = new_status
        session.commit()
        return True

    except Exception as e:
        session.rollback()
        logger.error("DB ERROR: %s", e)
        return False

    finally:
        session.close()
