from fastapi import APIRouter, Query

from scanner.core import OpportunityScanner

router = APIRouter()

_scanner: OpportunityScanner | None = None


def get_scanner() -> OpportunityScanner:
    global _scanner
    if _scanner is None:
        _scanner = OpportunityScanner()
    return _scanner


@router.get("/scanner/top-opportunities")
def get_top_opportunities(
    n: int = Query(5, ge=1, le=50),
    timeframe: str = Query("1h", pattern="^(1h|4h|1d)$"),
):
    scanner = get_scanner()
    ops = scanner.top_opportunities(n=n, timeframe=timeframe)
    return [
        {
            "rank": o.rank,
            "symbol": o.symbol,
            "side": o.side,
            "strategy": o.strategy,
            "score": o.score,
            "probability": o.probability_score,
            "risk_score": o.risk_score,
            "confidence": o.confidence,
            "price": o.price,
            "signals": o.signals,
            "probability_signals": o.probability_signals,
            "risk_signals": o.risk_signals,
        }
        for o in ops
    ]


@router.get("/scanner/dashboard")
def get_scanner_dashboard(
    n: int = Query(5, ge=1, le=50),
    timeframe: str = Query("1h", pattern="^(1h|4h|1d)$"),
):
    scanner = get_scanner()
    dashboard = scanner.get_dashboard(n=n, timeframe=timeframe)
    return {
        "symbols_scanned": dashboard.symbols_scanned,
        "opportunities_found": dashboard.opportunities_found,
        "top_opportunities": dashboard.top_opportunities,
        "top_signals": dashboard.top_signals,
        "market_summary": dashboard.market_summary,
        "intelligence_summary": dashboard.intelligence_summary,
        "timestamp": dashboard.timestamp,
    }
