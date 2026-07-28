#!/usr/bin/env python3
import sys
from datetime import datetime, timedelta, timezone
from database import (
    Base,
    engine,
    SessionLocal,
    Signal,
    Trade,
    PaperOrder,
    PaperTrade,
    JournalEntry,
    DecisionExplanation,
    Notification,
    Watchlist,
    User,
    OPEN,
    CLOSED,
    TP_HIT,
    SL_HIT,
    PENDING,
    FILLED,
    CANCEL,
)

def seed_database():
    print("Recreating database tables for SQLite...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        print("Seeding users...")
        test_user = User(
            id=1,
            username="test",
            email="test@example.com",
            hashed_password="$pbkdf2-sha256$29000$hQ...dummyhashedpassword", # just a placeholder
        )
        session.add(test_user)

        print("Seeding signals...")
        now = datetime.now(timezone.utc)

        # 1. Open Signal
        sig1 = Signal(
            id=1,
            symbol="BTCUSDT",
            side="LONG",
            timeframe="1h",
            price=96500.0,
            score=82.5,
            confidence=85.0,
            status="OPEN",
            approved=True,
            created_at=now - timedelta(hours=2),
        )

        # 2. Executed Signal
        sig2 = Signal(
            id=2,
            symbol="ETHUSDT",
            side="SHORT",
            timeframe="4h",
            price=2750.0,
            score=88.0,
            confidence=90.0,
            status="EXECUTED",
            approved=True,
            created_at=now - timedelta(days=1),
        )

        # 3. Rejected Signal
        sig3 = Signal(
            id=3,
            symbol="SOLUSDT",
            side="LONG",
            timeframe="15m",
            price=142.0,
            score=45.0,
            confidence=30.0,
            status="REJECTED",
            approved=False,
            reason="High risk level and poor trend indicator score",
            created_at=now - timedelta(hours=5),
        )

        session.add_all([sig1, sig2, sig3])

        print("Seeding trades (paper positions)...")
        # Trade 1: Open LONG position on BTCUSDT
        trade1 = Trade(
            id=1,
            signal_id=1,
            symbol="BTCUSDT",
            side="LONG",
            entry=96500.0,
            stop=95000.0,
            tp1=98500.0,
            tp2=100500.0,
            rr=1.33,
            pnl=250.0,  # current unrealized pnl
            status=OPEN,
            created_at=now - timedelta(hours=2),
        )

        # Trade 2: Closed SHORT position on ETHUSDT (TP Hit)
        trade2 = Trade(
            id=2,
            signal_id=2,
            symbol="ETHUSDT",
            side="SHORT",
            entry=2750.0,
            stop=2850.0,
            tp1=2600.0,
            tp2=2500.0,
            rr=1.5,
            pnl=150.0,  # realized pnl
            status=CLOSED,
            exit_price=2600.0,
            closed_at=now - timedelta(hours=12),
            close_reason=TP_HIT,
            created_at=now - timedelta(days=1),
        )

        session.add_all([trade1, trade2])

        print("Seeding paper orders & trades (Paper journal tables)...")
        order1 = PaperOrder(
            id=1,
            symbol="BTCUSDT",
            side="LONG",
            order_type="MARKET",
            quantity=0.05,
            price=96500.0,
            filled_price=96500.0,
            filled_quantity=0.05,
            status=FILLED,
            trade_id=1,
            created_at=now - timedelta(hours=2),
        )

        order2 = PaperOrder(
            id=2,
            symbol="ETHUSDT",
            side="SHORT",
            order_type="MARKET",
            quantity=1.0,
            price=2750.0,
            filled_price=2750.0,
            filled_quantity=1.0,
            status=FILLED,
            trade_id=2,
            created_at=now - timedelta(days=1),
        )

        session.add_all([order1, order2])

        paper_t1 = PaperTrade(
            id=1,
            position_id=1,
            order_id=1,
            symbol="BTCUSDT",
            side="LONG",
            entry=96500.0,
            quantity=0.05,
            pnl=250.0,
            status=OPEN,
            created_at=now - timedelta(hours=2),
        )

        paper_t2 = PaperTrade(
            id=2,
            position_id=2,
            order_id=2,
            symbol="ETHUSDT",
            side="SHORT",
            entry=2750.0,
            exit_price=2600.0,
            quantity=1.0,
            pnl=150.0,
            status=CLOSED,
            close_reason=TP_HIT,
            created_at=now - timedelta(days=1),
            closed_at=now - timedelta(hours=12),
        )

        session.add_all([paper_t1, paper_t2])

        print("Seeding journal entries...")
        journal1 = JournalEntry(
            id=1,
            symbol="BTCUSDT",
            side="LONG",
            entry_price=96500.0,
            score=82.5,
            confidence=85.0,
            entry_reason="Strong dynamic breakout aligned with dynamic Morning Brief recommendations",
            notes="Felt highly disciplined. Confident in the ATR multiplier support level.",
            result="PENDING",
            pnl=250.0,
            signal_id=1,
            trade_id=1,
            created_at=now - timedelta(hours=2),
        )

        journal2 = JournalEntry(
            id=2,
            symbol="ETHUSDT",
            side="SHORT",
            entry_price=2750.0,
            exit_price=2600.0,
            score=88.0,
            confidence=90.0,
            entry_reason="Resistance level breakout rejection on high 4h volume",
            exit_reason="Hit take profit target level 1",
            notes="Excellent trade execution. Kept emotion out of the closing decision.",
            result="WIN",
            pnl=150.0,
            signal_id=2,
            trade_id=2,
            created_at=now - timedelta(days=1),
        )

        session.add_all([journal1, journal2])

        print("Seeding decision explanations...")
        exp1 = DecisionExplanation(
            id=1,
            signal_id=1,
            symbol="BTC",
            side="LONG",
            decision="APPROVE",
            confidence=85.0,
            reasons=["Strong bull market regime detected", "BTC health is extremely strong", "EMA 20/50 golden cross"],
            warnings=["ATR shows slightly elevated volatility"],
            supporting_signals=["Trend score 0.9", "Volume ratio 1.8"],
            risk_notes=["Position size capped at $10k per trade engine limits"],
            summary="Strong bullish signals align across multi-timeframe engines. Safe entry level confirmed.",
            technical_score=0.9,
            whale_score=0.8,
            news_score=0.7,
            risk_score=0.1,  # low risk
            trend_score=0.9,
            portfolio_total_equity=10000.0,
            portfolio_unrealized_pnl=250.0,
            portfolio_realized_pnl=150.0,
            portfolio_exposure=4825.0,
            performance_sharpe=2.1,
            performance_sortino=2.5,
            performance_calmar=1.8,
            performance_profit_factor=1.9,
            created_at=now - timedelta(hours=2),
        )

        exp2 = DecisionExplanation(
            id=2,
            signal_id=2,
            symbol="ETH",
            side="SHORT",
            decision="STRONG_APPROVE",
            confidence=90.0,
            reasons=["MTF engines show bearish momentum in 1h, 4h", "Volume surge on resistance reject"],
            warnings=["Counter-trend to BTC overall bullishness"],
            supporting_signals=["MTF score 0.85"],
            risk_notes=["Risk multiplier restricted to standard 1.5 ATR"],
            summary="Clear MTF resistance rejection allows high-confidence SHORT play.",
            technical_score=0.85,
            whale_score=0.75,
            news_score=0.6,
            risk_score=0.2,
            trend_score=0.8,
            portfolio_total_equity=10000.0,
            portfolio_unrealized_pnl=250.0,
            portfolio_realized_pnl=150.0,
            portfolio_exposure=4825.0,
            performance_sharpe=2.1,
            performance_sortino=2.5,
            performance_calmar=1.8,
            performance_profit_factor=1.9,
            created_at=now - timedelta(days=1),
        )

        session.add_all([exp1, exp2])

        print("Seeding notifications...")
        notif1 = Notification(
            id=1,
            user_id=1,
            event_type="SIGNAL_APPROVED",
            payload={"symbol": "BTCUSDT", "side": "LONG", "price": 96500.0},
            read=False,
            created_at=now - timedelta(hours=2),
        )

        notif2 = Notification(
            id=2,
            user_id=1,
            event_type="TRADE_CLOSED",
            payload={"symbol": "ETHUSDT", "side": "SHORT", "pnl": 150.0, "reason": TP_HIT},
            read=True,
            created_at=now - timedelta(hours=12),
        )

        session.add_all([notif1, notif2])

        print("Seeding watchlists...")
        wl = Watchlist(
            id=1,
            user_id=1,
            name="Alpha Tracking",
            symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            created_at=now - timedelta(days=5),
        )
        session.add(wl)

        session.commit()
        print("Database seeding completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
