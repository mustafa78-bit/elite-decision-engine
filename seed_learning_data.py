import bcrypt
from datetime import datetime, timedelta, timezone
from database import get_session, create_tables, User, Signal, Trade, DecisionExplanation
from services.learning.decision_memory import DecisionMemoryService

def seed():
    create_tables()
    session = get_session()
    try:
        # Clear existing tables if any (to make it fully reproducible)
        session.query(User).delete()
        session.query(Signal).delete()
        session.query(Trade).delete()
        session.query(DecisionExplanation).delete()

        # 1. Create a Founder user
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(b"password123", salt).decode("utf-8")
        user = User(
            username="founder",
            email="founder@nexus.ai",
            hashed_password=hashed,
        )
        session.add(user)
        session.flush()

        # 2. Seed Signals & Trades & Explanations (12 sets)
        assets = [
            ("BTCUSDT", "LONG", 0.85, 0.75, 0.80, 0.15, 88.0, 150.0, "TAKE_PROFIT"),
            ("BTCUSDT", "LONG", 0.90, 0.80, 0.85, 0.10, 92.0, 320.0, "TAKE_PROFIT"),
            ("ETHUSDT", "LONG", 0.80, 0.70, 0.75, 0.20, 85.0, 110.0, "CLOSED"),
            ("SOLUSDT", "LONG", 0.75, 0.65, 0.70, 0.25, 80.0, -50.0, "STOP_LOSS"),
            ("BTCUSDT", "SHORT", 0.30, 0.35, 0.25, 0.80, 45.0, -120.0, "STOP_LOSS"),
            ("ETHUSDT", "SHORT", 0.25, 0.30, 0.20, 0.85, 40.0, -180.0, "CLOSED"),
            ("AVAXUSDT", "LONG", 0.82, 0.72, 0.78, 0.18, 86.0, 140.0, "TAKE_PROFIT"),
            ("SOLUSDT", "LONG", 0.88, 0.78, 0.82, 0.12, 90.0, 280.0, "TAKE_PROFIT"),
            # Pending ones (no closed trade, or open trades)
            ("BTCUSDT", "LONG", 0.70, 0.60, 0.65, 0.30, 75.0, 0.0, "OPEN"),
            ("ETHUSDT", "LONG", 0.68, 0.58, 0.62, 0.35, 72.0, 0.0, "OPEN"),
            ("LINKUSDT", "LONG", 0.65, 0.55, 0.60, 0.40, 70.0, 0.0, "OPEN"),
            ("UNIUSDT", "SHORT", 0.35, 0.40, 0.30, 0.75, 50.0, 0.0, "OPEN"),
        ]

        now = datetime.now(timezone.utc)

        for idx, (sym, side, trend, vol, btc, risk, conf, pnl, status) in enumerate(assets):
            created_time = now - timedelta(days=(12 - idx))

            sig = Signal(
                symbol=sym,
                side=side,
                timeframe="1h",
                price=50000.0 if "BTC" in sym else (3000.0 if "ETH" in sym else 100.0),
                trend_score=trend,
                volume_score=vol,
                btc_health=btc,
                risk_score=risk,
                confidence=conf,
                score=conf - 10.0,
                status="EXECUTED" if status in ("CLOSED", "TAKE_PROFIT", "STOP_LOSS") else "OPEN",
                reason=f"Pattern setup {idx}",
                created_at=created_time,
            )
            session.add(sig)
            session.flush()

            # Match Trade
            trade = Trade(
                signal_id=sig.id,
                symbol=sym,
                side=side,
                entry=sig.price,
                pnl=pnl,
                status=status,
                exit_price=sig.price * (1.0 + pnl/1000.0) if pnl != 0.0 else None,
                close_reason="Take Profit Hit" if "TAKE_PROFIT" in status else ("Stop Loss Hit" if "STOP_LOSS" in status else None),
                created_at=created_time,
                closed_at=created_time + timedelta(hours=4) if status in ("CLOSED", "TAKE_PROFIT", "STOP_LOSS") else None,
            )
            session.add(trade)
            session.flush()

            # Match Explanation
            reasons_list = [f"Strong trend momentum at {trend}"]
            if vol >= 0.7:
                reasons_list.append(f"High volume backing at {vol}")
            if risk <= 0.3:
                reasons_list.append(f"Low risk exposure verified ({risk})")

            expl = DecisionExplanation(
                signal_id=sig.id,
                symbol=sym,
                side=side,
                decision="BUY" if side == "LONG" else "SELL",
                confidence=conf,
                reasons=reasons_list,
                summary=f"Deterministic alignment setup for {sym} {side}",
                technical_score=trend,
                created_at=created_time,
            )
            session.add(expl)

        session.commit()
        print("Standard tables seeded successfully!")

        # 3. Trigger DecisionMemory sync to build the learning repository
        svc = DecisionMemoryService(session_factory=get_session)
        count = svc.sync_memories()
        print(f"Synced {count} decision memories from seeded data!")

    except Exception as e:
        session.rollback()
        print(f"Seeding failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed()
