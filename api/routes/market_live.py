import logging

from fastapi import APIRouter, Query

from market_data.live.engine import LiveMarketEngine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/market/live")
def get_market_live(
    symbol: str = Query("BTC"),
    timeframe: str = Query("1h"),
    limit: int = Query(100, ge=10, le=500),
):
    try:
        engine = LiveMarketEngine()
        snap = engine.snapshot(symbol=symbol, timeframe=timeframe, limit=limit)
        return {
            "symbol": snap.symbol,
            "price": snap.price,
            "volume_24h": snap.volume_24h,
            "change_24h": snap.change_24h,
            "high_24h": snap.high_24h,
            "low_24h": snap.low_24h,
            "timestamp": snap.timestamp,
            "candles": [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in snap.candles
            ],
        }
    except Exception as e:
        logger.error("Failed to get live market data: %s", e)
        return {"error": str(e)}
