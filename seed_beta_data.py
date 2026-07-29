import logging
from database import Signal, Trade, JournalEntry, User, SessionLocal, Base, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_beta_data")

def seed():
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        # Check if already seeded
        if session.query(User).filter(User.username == "founder_beta").first():
            logger.info("Database already seeded with founder_beta.")
            return

        logger.info("Seeding founder beta test user...")
        user = User(
            username="founder_beta",
            email="beta@nexus.com",
            hashed_password="hashed_placeholder_secure_jwt"
        )
        session.add(user)

        logger.info("Seeding test signals...")
        sig1 = Signal(
            symbol="BTCUSDT",
            side="LONG",
            timeframe="1h",
            price=50000.0,
            score=85.0,
            confidence=90.0,
            approved=True,
            status="CLOSED",
            reason="Strong trend alignment"
        )
        sig2 = Signal(
            symbol="ETHUSDT",
            side="SHORT",
            timeframe="1h",
            price=3000.0,
            score=45.0,
            confidence=60.0,
            approved=False,
            status="OPEN",
            reason="Whale distribution detected"
        )
        session.add_all([sig1, sig2])

        logger.info("Seeding test positions...")
        trade1 = Trade(
            signal_id=1,
            symbol="BTCUSDT",
            side="LONG",
            entry=50000.0,
            stop=49000.0,
            tp1=52000.0,
            tp2=55000.0,
            pnl=1500.0,
            status="CLOSED",
            close_reason="TAKE_PROFIT"
        )
        trade2 = Trade(
            signal_id=2,
            symbol="ETHUSDT",
            side="SHORT",
            entry=3000.0,
            stop=3100.0,
            tp1=2800.0,
            tp2=2600.0,
            pnl=0.0,
            status="OPEN"
        )
        session.add_all([trade1, trade2])

        logger.info("Seeding test journal entries...")
        je1 = JournalEntry(
            symbol="BTCUSDT",
            side="LONG",
            entry_price=50000.0,
            exit_price=52000.0,
            score=85.0,
            confidence=90.0,
            entry_reason="Strong trend alignment",
            exit_reason="Take profit targets hit cleanly",
            notes="Disciplined trade execution, minimal slippage.",
            result="WIN",
            pnl=1500.0,
            signal_id=1
        )
        session.add(je1)

        session.commit()
        logger.info("Seeding complete successfully!")
    except Exception as e:
        session.rollback()
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed()
