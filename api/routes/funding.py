import logging

from fastapi import APIRouter

from market_data.funding.collector import FundingCollector


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/funding")
def get_funding():
    logger.info("GET /funding")
    try:
        collector = FundingCollector()
        result = collector.fetch_all()
        items = []
        for rate in result.rates:
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
