import logging

from fastapi import APIRouter, Query

from market.provider import get_shared_multi_provider
from market_data.live.engine import LiveMarketEngine
from market_data.pivots import calculate_channel, calculate_divergence, calculate_levels

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


@router.get("/market/levels")
def get_market_levels(
    symbol: str = Query("BTC"),
    timeframe: str = Query("1h"),
    limit: int = Query(200, ge=10, le=500),
):
    try:
        collector = get_shared_multi_provider()
        df = collector.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        if df.empty:
            return []
        levels = calculate_levels(df)
        return levels
    except Exception as e:
        logger.error("Failed to calculate S/R levels: %s", e)
        return {"error": str(e)}


@router.get("/market/divergence")
def get_market_divergence(
    symbol: str = Query("BTC"),
    timeframe: str = Query("1h"),
    limit: int = Query(200, ge=10, le=500),
):
    try:
        collector = get_shared_multi_provider()
        df = collector.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        if df.empty:
            return {"found": False, "type": "none", "p1": None, "p2": None}
        div = calculate_divergence(df)
        return div
    except Exception as e:
        logger.error("Failed to calculate RSI divergence: %s", e)
        return {"error": str(e)}


@router.get("/market/channel")
def get_market_channel(
    symbol: str = Query("BTC"),
    timeframe: str = Query("1h"),
    limit: int = Query(200, ge=10, le=500),
):
    try:
        collector = get_shared_multi_provider()
        df = collector.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        if df.empty:
            return {"found": False, "direction": "none", "upper": None, "lower": None}
        channel = calculate_channel(df)
        return channel
    except Exception as e:
        logger.error("Failed to calculate trend channel: %s", e)
        return {"error": str(e)}
