from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from database import (
    Signal,
    Trade,
    JournalEntry,
    Notification,
    TelemetryEvent,
    User,
    create_tables,
    get_session,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed():
    logger.info("Initializing database tables...")
    create_tables()

    session = get_session()
    try:
        # Check if already seeded
        if session.query(User).count() > 0:
            logger.info("Database is already seeded. Skipping.")
            return

        logger.info("Seeding data...")

        # 1. Seed User
        user = User(
            username="founder",
            email="founder@nexus.ai",
            hashed_password="hashed_password_placeholder",
        )
        session.add(user)

        # 2. Seed Signals
        s1 = Signal(
            symbol="BTCUSDT",
            side="LONG",
            timeframe="1h",
            price=65000.0,
            score=88.5,
            confidence=85.0,
            status="EXECUTED",
            reason="Strong breakout above 200 EMA with volume support",
        )
        s2 = Signal(
            symbol="ETHUSDT",
            side="SHORT",
            timeframe="4h",
            price=3500.0,
            score=54.2,
            confidence=51.0,
            status="REJECTED",
            reason="Fails minimum score threshold (54.2 < 85)",
        )
        session.add_all([s1, s2])
        session.flush()

        # 3. Seed Trades (Positions)
        t1 = Trade(
            signal_id=s1.id,
            symbol="BTCUSDT",
            side="LONG",
            entry=65000.0,
            stop=64000.0,
            tp1=67000.0,
            tp2=69000.0,
            status="OPEN",
            pnl=250.0,
        )
        t2 = Trade(
            signal_id=None,
            symbol="SOLUSDT",
            side="LONG",
            entry=145.0,
            stop=140.0,
            tp1=155.0,
            status="CLOSED",
            exit_price=155.0,
            close_reason="TAKE_PROFIT",
            pnl=500.0,
            closed_at=datetime.now(timezone.utc),
        )
        session.add_all([t1, t2])

        # 4. Seed Journal
        j1 = JournalEntry(
            symbol="SOLUSDT",
            side="LONG",
            entry_price=145.0,
            exit_price=155.0,
            score=92.0,
            confidence=90.0,
            entry_reason="RSI bounce from support with news momentum",
            exit_reason="TP1 target achieved",
            notes="Felt extremely disciplined during this trade, no emotion.",
            result="WIN",
            pnl=500.0,
        )
        session.add(j1)

        # 5. Seed Notifications
        n1 = Notification(
            event_type="SIGNAL_CREATED",
            payload={"symbol": "BTCUSDT", "side": "LONG", "score": 88.5},
            read=False,
        )
        session.add(n1)

        # 6. Seed Telemetry Events
        now = datetime.now(timezone.utc)
        telemetry = [
            TelemetryEvent(screen="morning_brief", action="opened", duration=34.2, timestamp=now - timedelta(hours=4)),
            TelemetryEvent(screen="scanner", action="filters_changed", duration=12.5, timestamp=now - timedelta(hours=3)),
            TelemetryEvent(screen="decision_center", action="decision_opened", duration=45.0, timestamp=now - timedelta(hours=2.5)),
            TelemetryEvent(screen="execution", action="trade_executed", duration=6.4, timestamp=now - timedelta(hours=2)),
            TelemetryEvent(screen="journal", action="journal_written", duration=25.0, timestamp=now - timedelta(hours=1)),
            TelemetryEvent(screen="replay", action="replay_viewed", duration=120.0, timestamp=now - timedelta(minutes=30)),
            TelemetryEvent(screen="end_of_day", action="end_of_day_completed", duration=15.0, timestamp=now - timedelta(minutes=5)),
        ]
        session.add_all(telemetry)

        session.commit()
        logger.info("Successfully seeded database with high-fidelity Founder journey records!")
    except Exception as e:
        session.rollback()
        logger.error("Failed to seed database: %s", e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
