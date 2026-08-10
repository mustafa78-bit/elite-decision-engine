import logging

from fastapi import APIRouter

from config import FIXED_COIN_UNIVERSE
from market_data.funding.collector import FundingCollector

logger = logging.getLogger(__name__)
router = APIRouter()

# FundingCollector.fetch_all() returns Hyperliquid's entire listed universe
# (100+ perpetuals) -- FIXED_COIN_UNIVERSE ("BTCUSDT" style) is this app's
# actual scoped 25-coin universe, so bare-ticker-match against that instead
# of returning everything Hyperliquid happens to list.
_FIXED_UNIVERSE_BARE = {s.replace("USDT", "") for s in FIXED_COIN_UNIVERSE}


@router.get("/funding")
def get_funding():
    logger.info("GET /funding")
    try:
        collector = FundingCollector()
        result = collector.fetch_all()
        items = []
        for rate in result.rates:
            if rate.symbol not in _FIXED_UNIVERSE_BARE:
                continue
            items.append({
                "symbol": rate.symbol,
                "current_rate": rate.rate,
                "predicted_rate": rate.rate,
                "next_funding_time": (
                    rate.next_funding_time
                    if rate.next_funding_time
                    else "2026-07-11T12:00:00Z"
                ),
            })
        return {"funding": items}
    except Exception as e:
        logger.error("GET /funding failed: %s", e)
        return {"funding": [], "error": str(e)}
