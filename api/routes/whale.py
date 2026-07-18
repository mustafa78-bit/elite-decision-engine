import logging

from fastapi import APIRouter

from market.intelligence.whale import WhaleService
from market.services import MarketDataService

logger = logging.getLogger(__name__)
router = APIRouter()

_mip_service = None


def _get_mip():
    global _mip_service
    if _mip_service is None:
        _mip_service = MarketDataService()
    return _mip_service


@router.get("/whale/activity")
def get_whale_activity():
    symbols = ["BTC", "ETH"]
    activities = []
    mip = _get_mip()
    for sym in symbols:
        try:
            asset = mip.get_asset(sym)
            if asset.is_empty:
                continue
            indicators = asset.indicators
            ws = WhaleService()
            signals = ws.detect(
                symbol=sym,
                volume_score=indicators.get("volume_score"),
                volatility_score=indicators.get("volatility_score"),
                price=asset.price,
            )
            activities.extend(signals)
        except Exception:
            logger.warning("Whale detection failed for %s", sym, exc_info=True)
    return activities
