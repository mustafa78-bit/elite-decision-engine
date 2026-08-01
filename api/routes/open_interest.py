import logging

from fastapi import APIRouter, Query

from market_data.open_interest.collector import OpenInterestCollector


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/open-interest")
def get_open_interest(symbol: str = Query("BTC")):
    logger.info("GET /open-interest symbol=%s", symbol)
    try:
        collector = OpenInterestCollector()
        result = collector.fetch_all()
        items = []
        for record in result.records:
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
