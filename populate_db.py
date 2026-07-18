from datetime import datetime, timedelta, timezone
from database import get_session, Signal, Trade, create_tables

def populate():
    create_tables()
    session = get_session()

    # Clear existing to avoid double population
    session.query(Signal).delete()
    session.query(Trade).delete()

    now = datetime.utcnow()

    # 1. Add Signals
    s1 = Signal(
        symbol="BTC",
        side="LONG",
        timeframe="1h",
        price=43000.0,
        score=92.5,
        confidence=92.5,
        trend_score=0.95,
        volume_score=0.88,
        btc_health=0.90,
        risk_score=0.0,
        status="APPROVED",
        created_at=now - timedelta(minutes=10)
    )
    s2 = Signal(
        symbol="ETH",
        side="LONG",
        timeframe="1h",
        price=2300.0,
        score=78.2,
        confidence=78.2,
        trend_score=0.75,
        volume_score=0.80,
        btc_health=0.90,
        risk_score=0.1,
        status="APPROVED",
        created_at=now - timedelta(minutes=20)
    )
    s3 = Signal(
        symbol="SOL",
        side="SHORT",
        timeframe="1h",
        price=105.0,
        score=84.0,
        confidence=84.0,
        trend_score=0.85,
        volume_score=0.72,
        btc_health=0.90,
        risk_score=0.05,
        status="OPEN",
        created_at=now - timedelta(minutes=45)
    )
    session.add_all([s1, s2, s3])

    # 2. Add Trades (Open & Closed)
    t1 = Trade(
        symbol="BTCUSDT",
        side="LONG",
        entry=42500.0,
        status="OPEN",
        created_at=now - timedelta(hours=2)
    )
    t2 = Trade(
        symbol="ETHUSDT",
        side="LONG",
        entry=2250.0,
        exit_price=2310.0,
        pnl=600.0,
        status="TP_HIT",
        closed_at=now - timedelta(hours=1),
        created_at=now - timedelta(hours=3)
    )
    t3 = Trade(
        symbol="SOLUSDT",
        side="LONG",
        entry=100.0,
        exit_price=98.0,
        pnl=-200.0,
        status="SL_HIT",
        closed_at=now - timedelta(hours=4),
        created_at=now - timedelta(hours=5)
    )
    session.add_all([t1, t2, t3])

    session.commit()
    print("Database successfully populated with mock data.")
    session.close()

if __name__ == "__main__":
    populate()
