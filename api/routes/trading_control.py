from fastapi import APIRouter

from database import Signal, Trade, get_session
from exchange.binance.connector import BinanceExchange
from exchange.hyperliquid.connector import HyperliquidExchange

router = APIRouter()


@router.get("/trading-control")
def trading_control():
    session = get_session()
    try:
        open_signals = session.query(Signal).filter(Signal.status == "OPEN").count()
        approved = session.query(Signal).filter(Signal.approved == True).count()
        total_signals = session.query(Signal).count()

        open_trades = session.query(Trade).filter(Trade.status == "OPEN").count()
        closed = session.query(Trade).filter(Trade.status.in_(["CLOSED", "TP_HIT", "SL_HIT"])).count()
        total_trades = session.query(Trade).count()
    finally:
        session.close()

    hl = HyperliquidExchange()
    bn = BinanceExchange()

    exchanges = [
        {
            "name": hl.name,
            "trading_enabled": hl.trading_enabled(),
            "status": "connected",
        },
        {
            "name": bn.name,
            "trading_enabled": bn.trading_enabled(),
            "status": "connected",
        },
    ]

    return {
        "exchanges": exchanges,
        "signals": {
            "total": total_signals,
            "open": open_signals,
            "approved": approved,
        },
        "trades": {
            "total": total_trades,
            "open": open_trades,
            "closed": closed,
        },
        "shadow": {
            "mode": "active",
            "engine": "ShadowEngine v1",
        },
        "risk": {
            "max_open_trades": 3,
            "max_daily_loss": 10000,
        },
    }
