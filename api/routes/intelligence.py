from fastapi import APIRouter

from database import Signal, Trade, get_session
from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.volatility import VolatilityEngine
from scoring.regime_engine import RegimeEngine
from market_data.btc_health import BTCHealth

router = APIRouter()

FINAL_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})


@router.get("/intelligence")
def get_intelligence():
    market_data = {}
    try:
        collector = HyperliquidCollector()
        indicators = IndicatorEngine()
        btc = BTCHealth()
        vol = VolatilityEngine()
        regime = RegimeEngine()

        df = collector.get_ohlcv(symbol="BTC", timeframe="1h")
        if not df.empty:
            values = indicators.calculate(df)
            btc_score = btc.score()
            vol_score = vol.score(values)
            reg = regime.detect(values)
            market_data = {
                "price": float(df["close"].iloc[-1]),
                "regime": reg["regime"],
                "btc_health": btc_score,
                "volatility": vol_score["volatility"],
                "rsi": round(values["rsi"], 2),
            }
    except Exception:
        market_data = {"error": "Market data unavailable"}

    session = get_session()
    try:
        all_signals = session.query(Signal).all()
        all_trades = session.query(Trade).all()
    finally:
        session.close()

    open_signals = [s for s in all_signals if str(s.status) == "OPEN"]
    approved = len([s for s in all_signals if str(s.status) in {"EXECUTED", "OPEN"}])
    rejected = len([s for s in all_signals if str(s.status) == "REJECTED"])

    open_trades = [t for t in all_trades if str(t.status) == "OPEN"]
    closed_trades = [t for t in all_trades if str(t.status) in FINAL_STATUSES]
    total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)

    return {
        "market": market_data,
        "signals": {
            "total": len(all_signals),
            "open": len(open_signals),
            "approved": approved,
            "rejected": rejected,
        },
        "risk": {
            "open_trades": len(open_trades),
            "max_open_trades": 3,
        },
        "trades": {
            "open": len(open_trades),
            "closed": len(closed_trades),
            "total_pnl": round(total_pnl, 2),
        },
    }
