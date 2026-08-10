import logging

from fastapi import APIRouter, Query

from config import FIXED_COIN_UNIVERSE
from market_data.open_interest.collector import OpenInterestCollector

logger = logging.getLogger(__name__)
router = APIRouter()

# OpenInterestCollector.fetch_all() returns Hyperliquid's entire listed
# universe (100+ perpetuals) -- FIXED_COIN_UNIVERSE ("BTCUSDT" style) is
# this app's actual scoped 25-coin universe, so bare-ticker-match against
# that instead of returning everything Hyperliquid happens to list.
_FIXED_UNIVERSE_BARE = {s.replace("USDT", "") for s in FIXED_COIN_UNIVERSE}


@router.get("/open-interest")
def get_open_interest(symbol: str = Query("BTC")):
    logger.info("GET /open-interest symbol=%s", symbol)
    try:
        collector = OpenInterestCollector()
        result = collector.fetch_all()
        items = []
        for record in result.records:
            if record.symbol not in _FIXED_UNIVERSE_BARE:
                continue
            trend = collector.fetch_with_trend(record.symbol)
            items.append({
                "symbol": record.symbol,
                "open_interest": record.value,
                "change_24h": round(trend.get("strength", 0) * 100, 2),
                "volume": record.value,
            })
        if not items:
            return {"open_interest": []}
        return {"open_interest": items}
    except Exception as e:
        logger.error("GET /open-interest failed: %s", e)
        return {"open_interest": [], "error": str(e)}
