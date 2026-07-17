from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
)

DB_HOST = POSTGRES_HOST or "localhost"
DB_PORT = POSTGRES_PORT or "5432"
DB_NAME = POSTGRES_DB or "decision_engine"
DB_USER = POSTGRES_USER or "postgres"
DB_PASSWORD = POSTGRES_PASSWORD or "postgres"

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

# -----------------------------------------------------------------------------
# SIGNAL TABLE
# -----------------------------------------------------------------------------

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True)
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())

# -----------------------------------------------------------------------------
# TRADE TABLE
# -----------------------------------------------------------------------------

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
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

    exchange_order_id = Column(String(120))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

def get_session():
    return SessionLocal()


def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("Database initialized successfully.")
