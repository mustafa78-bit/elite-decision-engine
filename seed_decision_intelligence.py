#!/usr/bin/env python
"""Seeding script for the Decision Intelligence Center.

Populates high-fidelity, realistic signals (decisions), trades, paper trades,
and paper orders spanning multiple assets, market regimes, outcomes, and metrics.
"""

from datetime import datetime, timedelta, timezone
import logging
import sys

from database import Signal, Trade, PaperTrade, PaperOrder, get_session, create_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


def seed_data():
    create_tables()
    session = get_session()

    try:
        logger.info("Clearing existing database records to ensure clean seeding...")
        session.query(Signal).delete()
        session.query(Trade).delete()
        session.query(PaperTrade).delete()
        session.query(PaperOrder).delete()
        session.commit()

        now = datetime.now(timezone.utc)

        # 1. High-fidelity signals (decisions)
        signals_data = [
            # STRONG_BUY Setup (Win)
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "timeframe": "1h",
                "divergence": "Bullish divergence on RSI",
                "price": 62500.0,
                "score": 0.88,
                "confidence": 95.0,
                "market_health": 0.85,
                "btc_health": 0.90,
                "volume_score": 0.82,
                "funding_score": 0.60,
                "oi_score": 0.75,
                "cvd_score": 0.70,
                "trend_score": 0.85,
                "risk_score": 0.15,
                "approved": True,
                "status": "EXECUTED",
                "reason": "Closed on Take Profit hit",
                "created_at": now - timedelta(days=5),
            },
            # BUY Setup (Win)
            {
                "symbol": "ETHUSDT",
                "side": "LONG",
                "timeframe": "4h",
                "divergence": "EMA trend alignment",
                "price": 3120.0,
                "score": 0.81,
                "confidence": 85.0,
                "market_health": 0.75,
                "btc_health": 0.80,
                "volume_score": 0.78,
                "funding_score": 0.55,
                "oi_score": 0.68,
                "cvd_score": 0.65,
                "trend_score": 0.79,
                "risk_score": 0.22,
                "approved": True,
                "status": "EXECUTED",
                "reason": "Closed on Target 1 hit",
                "created_at": now - timedelta(days=4),
            },
            # WATCH Setup (Neutral)
            {
                "symbol": "SOLUSDT",
                "side": "LONG",
                "timeframe": "15m",
                "divergence": "Mean reversion pattern",
                "price": 142.5,
                "score": 0.65,
                "confidence": 72.0,
                "market_health": 0.50,
                "btc_health": 0.55,
                "volume_score": 0.48,
                "funding_score": 0.50,
                "oi_score": 0.52,
                "cvd_score": 0.49,
                "trend_score": 0.55,
                "risk_score": 0.45,
                "approved": False,
                "status": "OPEN",
                "reason": "Confidence below threshold, watching swing levels",
                "created_at": now - timedelta(days=3),
            },
            # REJECT Setup (False Positive / Loss)
            {
                "symbol": "AVAXUSDT",
                "side": "SHORT",
                "timeframe": "1h",
                "divergence": "Overbought reversal",
                "price": 28.40,
                "score": 0.52,
                "confidence": 62.0,
                "market_health": 0.40,
                "btc_health": 0.35,
                "volume_score": 0.45,
                "funding_score": 0.40,
                "oi_score": 0.38,
                "cvd_score": 0.42,
                "trend_score": 0.38,
                "risk_score": 0.65,
                "approved": False,
                "status": "REJECTED",
                "reason": "Rejected by Risk Manager: High correlation risk and weak trend definition",
                "created_at": now - timedelta(days=2),
            },
            # STRONG_SELL Setup (Loss)
            {
                "symbol": "LINKUSDT",
                "side": "SHORT",
                "timeframe": "4h",
                "divergence": "Bearish breakdown",
                "price": 15.20,
                "score": 0.45,
                "confidence": 58.0,
                "market_health": 0.30,
                "btc_health": 0.25,
                "volume_score": 0.35,
                "funding_score": 0.30,
                "oi_score": 0.28,
                "cvd_score": 0.32,
                "trend_score": 0.29,
                "risk_score": 0.70,
                "approved": True,
                "status": "EXECUTED",
                "reason": "Closed on Stop Loss hit",
                "created_at": now - timedelta(days=1),
            },
            # Active OPEN Setup (Executed / Open Trade)
            {
                "symbol": "ADAUSDT",
                "side": "LONG",
                "timeframe": "1h",
                "divergence": "Double bottom breakout",
                "price": 0.38,
                "score": 0.84,
                "confidence": 88.0,
                "market_health": 0.78,
                "btc_health": 0.82,
                "volume_score": 0.80,
                "funding_score": 0.58,
                "oi_score": 0.72,
                "cvd_score": 0.68,
                "trend_score": 0.82,
                "risk_score": 0.18,
                "approved": True,
                "status": "OPEN",
                "reason": "Position entered, trailing stop active",
                "created_at": now - timedelta(hours=6),
            },
        ]

        logger.info("Inserting seeded Signals...")
        inserted_signals = []
        for s_data in signals_data:
            s = Signal(**s_data)
            session.add(s)
            session.flush()  # to populate id
            inserted_signals.append(s)

        # 2. Matching Trades to construct outcome and performance DTOs
        trades_data = [
            # BTC Win (Matching Signal 0)
            {
                "signal_id": inserted_signals[0].id,
                "symbol": "BTCUSDT",
                "side": "LONG",
                "entry": 62500.0,
                "stop": 61250.0,
                "tp1": 65000.0,
                "tp2": 67500.0,
                "rr": 2.0,
                "pnl": 2500.0,
                "status": "CLOSED",
                "exit_price": 65000.0,
                "close_reason": "TP_HIT",
                "exchange_order_id": "hl-order-btc-1",
                "created_at": inserted_signals[0].created_at,
                "closed_at": inserted_signals[0].created_at + timedelta(days=1),
            },
            # ETH Win (Matching Signal 1)
            {
                "signal_id": inserted_signals[1].id,
                "symbol": "ETHUSDT",
                "side": "LONG",
                "entry": 3120.0,
                "stop": 3050.0,
                "tp1": 3260.0,
                "tp2": 3400.0,
                "rr": 2.0,
                "pnl": 560.0,
                "status": "CLOSED",
                "exit_price": 3260.0,
                "close_reason": "TP_HIT",
                "exchange_order_id": "hl-order-eth-1",
                "created_at": inserted_signals[1].created_at,
                "closed_at": inserted_signals[1].created_at + timedelta(days=1),
            },
            # LINK Loss (Matching Signal 4)
            {
                "signal_id": inserted_signals[4].id,
                "symbol": "LINKUSDT",
                "side": "SHORT",
                "entry": 15.20,
                "stop": 15.80,
                "tp1": 14.00,
                "tp2": 13.00,
                "rr": 2.0,
                "pnl": -300.0,
                "status": "CLOSED",
                "exit_price": 15.80,
                "close_reason": "SL_HIT",
                "exchange_order_id": "hl-order-link-1",
                "created_at": inserted_signals[4].created_at,
                "closed_at": inserted_signals[4].created_at + timedelta(hours=12),
            },
            # ADA Active Open (Matching Signal 5)
            {
                "signal_id": inserted_signals[5].id,
                "symbol": "ADAUSDT",
                "side": "LONG",
                "entry": 0.38,
                "stop": 0.365,
                "tp1": 0.41,
                "tp2": 0.44,
                "rr": 2.0,
                "pnl": 50.0,  # Unreleased / live PnL
                "status": "OPEN",
                "exit_price": None,
                "close_reason": None,
                "exchange_order_id": "hl-order-ada-1",
                "created_at": inserted_signals[5].created_at,
                "closed_at": None,
            },
        ]

        logger.info("Inserting seeded Trades (positions)...")
        inserted_trades = []
        for t_data in trades_data:
            t = Trade(**t_data)
            session.add(t)
            session.flush()
            inserted_trades.append(t)

        # 3. Seed PaperTrade database records (needed for execution performance summary KPIs!)
        paper_trades_data = [
            # BTC Win (Matching Signal 0 / Position 0)
            {
                "position_id": inserted_trades[0].id,
                "order_id": 1,
                "symbol": "BTCUSDT",
                "side": "LONG",
                "entry": 62500.0,
                "exit_price": 65000.0,
                "quantity": 1.0,
                "pnl": 2500.0,
                "status": "TAKE_PROFIT",
                "close_reason": "TP_HIT",
                "created_at": inserted_trades[0].created_at,
                "closed_at": inserted_trades[0].closed_at,
            },
            # ETH Win (Matching Signal 1 / Position 1)
            {
                "position_id": inserted_trades[1].id,
                "order_id": 2,
                "symbol": "ETHUSDT",
                "side": "LONG",
                "entry": 3120.0,
                "exit_price": 3260.0,
                "quantity": 4.0,
                "pnl": 560.0,
                "status": "TAKE_PROFIT",
                "close_reason": "TP_HIT",
                "created_at": inserted_trades[1].created_at,
                "closed_at": inserted_trades[1].closed_at,
            },
            # LINK Loss (Matching Signal 4 / Position 2)
            {
                "position_id": inserted_trades[2].id,
                "order_id": 3,
                "symbol": "LINKUSDT",
                "side": "SHORT",
                "entry": 15.20,
                "exit_price": 15.80,
                "quantity": 500.0,
                "pnl": -300.0,
                "status": "STOP_LOSS",
                "close_reason": "SL_HIT",
                "created_at": inserted_trades[2].created_at,
                "closed_at": inserted_trades[2].closed_at,
            },
            # ADA Active Open (Matching Signal 5 / Position 3)
            {
                "position_id": inserted_trades[3].id,
                "order_id": 4,
                "symbol": "ADAUSDT",
                "side": "LONG",
                "entry": 0.38,
                "exit_price": None,
                "quantity": 1000.0,
                "pnl": 0.0,
                "status": "OPEN",
                "close_reason": None,
                "created_at": inserted_trades[3].created_at,
                "closed_at": None,
            },
        ]

        logger.info("Inserting seeded PaperTrades...")
        for pt_data in paper_trades_data:
            pt = PaperTrade(**pt_data)
            session.add(pt)

        # 4. Seed PaperOrder database records
        paper_orders_data = [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "order_type": "MARKET",
                "quantity": 1.0,
                "price": 62500.0,
                "filled_price": 62500.0,
                "filled_quantity": 1.0,
                "status": "FILLED",
                "trade_id": 1,
                "reason": "Signal execution entry",
                "created_at": now - timedelta(days=5),
            },
            {
                "symbol": "ETHUSDT",
                "side": "LONG",
                "order_type": "MARKET",
                "quantity": 4.0,
                "price": 3120.0,
                "filled_price": 3120.0,
                "filled_quantity": 4.0,
                "status": "FILLED",
                "trade_id": 2,
                "reason": "Signal execution entry",
                "created_at": now - timedelta(days=4),
            },
            {
                "symbol": "LINKUSDT",
                "side": "SHORT",
                "order_type": "MARKET",
                "quantity": 500.0,
                "price": 15.20,
                "filled_price": 15.20,
                "filled_quantity": 500.0,
                "status": "FILLED",
                "trade_id": 3,
                "reason": "Signal execution entry",
                "created_at": now - timedelta(days=1),
            },
        ]

        logger.info("Inserting seeded PaperOrders...")
        for po_data in paper_orders_data:
            po = PaperOrder(**po_data)
            session.add(po)

        session.commit()
        logger.info("Successfully seeded database for Decision Intelligence Center!")

    except Exception as e:
        session.rollback()
        logger.error("Seeding failed: %s", e)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    seed_data()
