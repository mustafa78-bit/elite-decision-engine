import logging
import os
import sys
from datetime import datetime, timedelta, timezone
import bcrypt

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

# Ensure PYTHONPATH includes the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ACCOUNT_EQUITY
from database import (
    create_tables,
    get_session,
    User,
    UserSettings,
    Signal,
    Trade,
    Notification,
    Watchlist,
    JournalEntry,
    PaperOrder,
    PaperTrade,
    DecisionExplanation,
)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def seed():
    logger.info("Initializing database tables...")
    create_tables()

    session = get_session()
    try:
        # Check if user already exists
        mustafa = session.query(User).filter(User.username == "mustafa").first()
        if not mustafa:
            logger.info("Seeding user 'mustafa'...")
            mustafa = User(
                username="mustafa",
                email="mustafa@founder.alpha",
                hashed_password=hash_password("password123"),
            )
            session.add(mustafa)
            session.commit()
            logger.info("User 'mustafa' seeded successfully.")
        else:
            logger.info("User 'mustafa' already exists.")

        # Seed UserSettings
        settings = session.query(UserSettings).filter(UserSettings.user_id == mustafa.id).first()
        if not settings:
            logger.info("Seeding user settings...")
            settings = UserSettings(
                user_id=mustafa.id,
                timezone="UTC",
                theme="light",
                dashboard_config={"layout": "default"},
                risk_preferences={"max_loss": 10000},
            )
            session.add(settings)

        # Seed Watchlist
        wl = session.query(Watchlist).filter(Watchlist.user_id == mustafa.id).first()
        if not wl:
            logger.info("Seeding watchlist...")
            wl = Watchlist(
                user_id=mustafa.id,
                name="Default Core Watchlist",
                symbols=["BTC", "ETH", "SOL", "LINK", "AVAX", "ARB"],
            )
            session.add(wl)

        # Clear existing signals and trades to prevent duplication
        session.query(Signal).delete()
        session.query(Trade).delete()
        session.query(Notification).delete()
        session.query(JournalEntry).delete()
        session.query(PaperOrder).delete()
        session.query(PaperTrade).delete()
        session.query(DecisionExplanation).delete()

        logger.info("Seeding high-fidelity signals...")
        # Create signals
        signals_data = [
            Signal(
                symbol="BTC", side="LONG", timeframe="1h", divergence="BULLISH_RSI",
                price=64500.0, score=92.5, confidence=0.88, market_health=0.85, btc_health=0.90,
                volume_score=0.90, funding_score=0.80, oi_score=0.85, cvd_score=0.75, trend_score=0.95,
                risk_score=0.90, approved=True, status="CLOSED", reason="Strong breakout above 64k with heavy volume confirmation."
            ),
            Signal(
                symbol="ETH", side="LONG", timeframe="1h", divergence="BULLISH_MACD",
                price=3450.0, score=88.0, confidence=0.82, market_health=0.80, btc_health=0.90,
                volume_score=0.85, funding_score=0.70, oi_score=0.80, cvd_score=0.70, trend_score=0.90,
                risk_score=0.85, approved=True, status="OPEN", reason="Consolidation break-up, lagging BTC but volume is picking up."
            ),
            Signal(
                symbol="SOL", side="LONG", timeframe="1h", divergence="NONE",
                price=142.5, score=91.0, confidence=0.85, market_health=0.85, btc_health=0.90,
                volume_score=0.95, funding_score=0.75, oi_score=0.90, cvd_score=0.80, trend_score=0.95,
                risk_score=0.80, approved=True, status="OPEN", reason="Massive buying pressure, high relative volume index."
            ),
            Signal(
                symbol="LINK", side="SHORT", timeframe="1h", divergence="BEARISH_RSI",
                price=15.2, score=65.0, confidence=0.55, market_health=0.50, btc_health=0.50,
                volume_score=0.40, funding_score=0.50, oi_score=0.45, cvd_score=0.35, trend_score=0.60,
                risk_score=0.50, approved=False, status="REJECTED", reason="Counter-trend, rejected by risk manager due to high volatility."
            ),
        ]
        session.add_all(signals_data)
        session.commit()

        # Retrieve seeded signals for referencing ids
        seeded_signals = session.query(Signal).all()
        sig_map = {s.symbol: s.id for s in seeded_signals}

        logger.info("Seeding high-fidelity trades...")
        now_naive = datetime.now()
        # Seed trades
        trades_data = [
            # Closed Winning Trades
            Trade(
                signal_id=sig_map.get("BTC"), symbol="BTC", side="LONG",
                entry=63100.0, stop=62100.0, tp1=64500.0, tp2=65500.0, rr=1.4,
                pnl=1400.0, status="CLOSED", exit_price=64500.0,
                closed_at=now_naive - timedelta(days=2), close_reason="TAKE_PROFIT",
                exchange_order_id="HL-ORD-10023", created_at=now_naive - timedelta(days=2, hours=4)
            ),
            Trade(
                signal_id=sig_map.get("ETH"), symbol="ETH", side="LONG",
                entry=3320.0, stop=3250.0, tp1=3450.0, tp2=3550.0, rr=1.85,
                pnl=950.0, status="CLOSED", exit_price=3450.0,
                closed_at=now_naive - timedelta(days=1), close_reason="TAKE_PROFIT",
                exchange_order_id="HL-ORD-10024", created_at=now_naive - timedelta(days=1, hours=8)
            ),
            # Closed Losing Trade
            Trade(
                signal_id=None, symbol="SOL", side="LONG",
                entry=145.0, stop=141.0, tp1=152.0, tp2=158.0, rr=1.75,
                pnl=-400.0, status="CLOSED", exit_price=141.0,
                closed_at=now_naive - timedelta(hours=12), close_reason="STOP_LOSS",
                exchange_order_id="HL-ORD-10025", created_at=now_naive - timedelta(hours=18)
            ),
            # Open Active Trades
            Trade(
                signal_id=sig_map.get("ETH"), symbol="ETH", side="LONG",
                entry=3410.0, stop=3340.0, tp1=3550.0, tp2=3650.0, rr=2.0,
                pnl=120.0, status="OPEN", exit_price=None,
                closed_at=None, close_reason=None,
                exchange_order_id="HL-ORD-10026", created_at=now_naive - timedelta(hours=4)
            ),
            Trade(
                signal_id=sig_map.get("SOL"), symbol="SOL", side="LONG",
                entry=141.5, stop=138.0, tp1=149.0, tp2=155.0, rr=2.1,
                pnl=35.0, status="OPEN", exit_price=None,
                closed_at=None, close_reason=None,
                exchange_order_id="HL-ORD-10027", created_at=now_naive - timedelta(hours=2)
            ),
        ]
        session.add_all(trades_data)
        session.commit()

        logger.info("Seeding notifications...")
        notifications_data = [
            Notification(
                user_id=mustafa.id, event_type="TRADE_OPENED",
                payload={"trade_id": 4, "symbol": "ETH", "side": "LONG", "price": 3410.0, "pnl": 0.0, "intelligence": "AI consensus: STRONG BUY - Trend Strategy aligns with massive spot volume."},
                read=False, created_at=now_naive - timedelta(hours=4)
            ),
            Notification(
                user_id=mustafa.id, event_type="TRADE_OPENED",
                payload={"trade_id": 5, "symbol": "SOL", "side": "LONG", "price": 141.5, "pnl": 0.0, "intelligence": "OLLO: Alert! Whale transaction of 50,000 SOL detected near local support."},
                read=False, created_at=now_naive - timedelta(hours=2)
            ),
            Notification(
                user_id=mustafa.id, event_type="TRADE_CLOSED",
                payload={"trade_id": 3, "symbol": "SOL", "side": "LONG", "price": 141.0, "pnl": -400.0, "intelligence": "Risk Manager: Trade closed due to Stop Loss hit at $141.0."},
                read=True, created_at=now_naive - timedelta(hours=12)
            ),
        ]
        session.add_all(notifications_data)

        logger.info("Seeding trade journal entries...")
        journal_data = [
            JournalEntry(
                symbol="BTC", side="LONG", entry_price=63100.0, exit_price=64500.0,
                score=92.5, confidence=0.88, entry_reason="Strong weekly breakout above consolidation.",
                exit_reason="Reached target resistance zone near 64.5k.",
                notes="Perfect execution, no emotional decisions.", result="WIN", pnl=1400.0,
                created_at=now_naive - timedelta(days=2)
            ),
            JournalEntry(
                symbol="ETH", side="LONG", entry_price=3320.0, exit_price=3450.0,
                score=88.0, confidence=0.82, entry_reason="Bullish divergence on hourly MACD.",
                exit_reason="Reached first profit target.",
                notes="Slight delay on entry execution, but did not hurt final outcome.", result="WIN", pnl=950.0,
                created_at=now_naive - timedelta(days=1)
            ),
            JournalEntry(
                symbol="SOL", side="LONG", entry_price=145.0, exit_price=141.0,
                score=78.0, confidence=0.72, entry_reason="Attempted momentum catch of breakout candle.",
                exit_reason="Faked out, stop loss triggered perfectly.",
                notes="Breakout volume was too low in retrospect. Need to wait for hourly candle close.", result="LOSS", pnl=-400.0,
                created_at=now_naive - timedelta(hours=12)
            ),
        ]
        session.add_all(journal_data)

        logger.info("Seeding paper trading logs...")
        orders_data = [
            PaperOrder(symbol="BTC", side="LONG", order_type="LIMIT", quantity=0.2, price=63100.0, filled_price=63100.0, filled_quantity=0.2, status="FILLED", trade_id=1),
            PaperOrder(symbol="ETH", side="LONG", order_type="LIMIT", quantity=3.0, price=3320.0, filled_price=3320.0, filled_quantity=3.0, status="FILLED", trade_id=2),
            PaperOrder(symbol="SOL", side="LONG", order_type="MARKET", quantity=25.0, price=145.0, filled_price=145.0, filled_quantity=25.0, status="FILLED", trade_id=3),
        ]
        session.add_all(orders_data)

        paper_trades_data = [
            PaperTrade(position_id=1, order_id=1, symbol="BTC", side="LONG", entry=63100.0, exit_price=64500.0, quantity=0.2, pnl=1400.0, status="CLOSED", close_reason="TP_HIT", closed_at=now_naive - timedelta(days=2)),
            PaperTrade(position_id=2, order_id=2, symbol="ETH", side="LONG", entry=3320.0, exit_price=3450.0, quantity=3.0, pnl=950.0, status="CLOSED", close_reason="TP_HIT", closed_at=now_naive - timedelta(days=1)),
            PaperTrade(position_id=3, order_id=3, symbol="SOL", side="LONG", entry=145.0, exit_price=141.0, quantity=25.0, pnl=-400.0, status="CLOSED", close_reason="SL_HIT", closed_at=now_naive - timedelta(hours=12)),
        ]
        session.add_all(paper_trades_data)

        logger.info("Seeding decision explanations...")
        exp_data = [
            DecisionExplanation(
                signal_id=sig_map.get("BTC") or 1, symbol="BTC", side="LONG",
                decision="LONG", confidence=0.88,
                reasons=[
                    "Weekly breakout above 63k consolidation zone with heavy volume confirmation.",
                    "RSI divergence bullish signal confirmed on the 1h timeframe.",
                    "Active retail & institutional bid interest seen via Hyperliquid order book analysis."
                ],
                warnings=[
                    "Slight bearish divergence on the 5m scalp timeframe.",
                    "Funding rate is elevated at +0.015%, minor leverage wash risk."
                ],
                supporting_signals=[
                    "RSI Divergence: Strong Bullish",
                    "EMA Cloud (20/50/200): Bullish alignment",
                    "Volume Delta: High buying imbalance (+3.4M USD)"
                ],
                risk_notes=[
                    "Max portfolio exposure is within safe limits (current 1.4% total risk).",
                    "Stop loss set at $62,100, which is below key support level (1.5x ATR)."
                ],
                summary="The AI Council reached a consensus of 92.5% confidence for a LONG entry on BTC. This is supported by strong volume expansion and multi-timeframe trend alignment. High probability of continuation.",
                technical_score=0.92, whale_score=0.88, news_score=0.85, risk_score=0.90, trend_score=0.95,
                portfolio_total_equity=ACCOUNT_EQUITY + 1950.0, portfolio_unrealized_pnl=155.0, portfolio_realized_pnl=1950.0, portfolio_exposure=4500.0,
                performance_sharpe=2.45, performance_sortino=2.88, performance_calmar=3.10, performance_profit_factor=5.87
            ),
            DecisionExplanation(
                signal_id=sig_map.get("ETH") or 2, symbol="ETH", side="LONG",
                decision="LONG", confidence=0.82,
                reasons=[
                    "Lagging BTC trend breakout, typical second-leg behavior.",
                    "Bullish divergence on hourly MACD confirms local bottom has formed.",
                    "Whale wallets adding spot positions near key support ($3,320)."
                ],
                warnings=[
                    "Overhead resistance at $3,550 may slow down immediate continuation."
                ],
                supporting_signals=[
                    "MACD Divergence: Confirmed Bullish",
                    "Whale Flow: Inflow +$14.2M over 24h",
                    "Liquidity Pools: Bid-side thickness increased near entry"
                ],
                risk_notes=[
                    "Position sizing calculated at 1.0% trade risk ($100), quantity is 3.0 ETH."
                ],
                summary="High confidence consensus established on ETH LONG. Technical setup is highly symmetric with lag-response play typical of late consolidation phases. Risk/reward ratio is highly favorable (1.85).",
                technical_score=0.88, whale_score=0.92, news_score=0.80, risk_score=0.85, trend_score=0.90,
                portfolio_total_equity=ACCOUNT_EQUITY + 1950.0, portfolio_unrealized_pnl=155.0, portfolio_realized_pnl=1950.0, portfolio_exposure=4500.0,
                performance_sharpe=2.45, performance_sortino=2.88, performance_calmar=3.10, performance_profit_factor=5.87
            )
        ]
        session.add_all(exp_data)

        session.commit()
        logger.info("Database seeding successfully completed with high-fidelity, comprehensive telemetry.")

    except Exception as e:
        session.rollback()
        logger.error("Seeding failed: %s", e)
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    seed()
