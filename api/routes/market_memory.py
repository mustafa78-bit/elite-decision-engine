from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.market_memory_service import MarketMemoryService

router = APIRouter(prefix="/api/v1/market-memory")


class MarketMemoryResponse(BaseModel):
    id: int
    symbol: str
    regime_type: str
    volatility_metric: float | None = None
    rsi_14: float | None = None
    funding_rate: float


class MarketMemoryRecordRequest(BaseModel):
    symbol: str
    price: float
    ema20: float
    ema50: float
    ema200: float
    atr: float
    rsi: float
    funding_rate: float = 0.0


def _get_market_memory_service() -> MarketMemoryService:
    return MarketMemoryService()


@router.post("/snapshot", response_model=MarketMemoryResponse)
def record_snapshot(body: MarketMemoryRecordRequest):
    svc = _get_market_memory_service()
    try:
        snap = svc.record_regime_snapshot(
            symbol=body.symbol.upper(),
            price=body.price,
            ema20=body.ema20,
            ema50=body.ema50,
            ema200=body.ema200,
            atr=body.atr,
            rsi=body.rsi,
            funding_rate=body.funding_rate
        )
        return MarketMemoryResponse(
            id=snap["id"],
            symbol=snap["symbol"],
            regime_type=snap["regime_type"],
            volatility_metric=snap["volatility_metric"],
            rsi_14=snap["rsi_14"],
            funding_rate=snap["funding_rate"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record market memory snapshot: {e}")


@router.get("", response_model=List[MarketMemoryResponse])
def get_similar_contexts(regime: str = "TREND", limit: int = 5):
    svc = _get_market_memory_service()
    try:
        snaps = svc.get_similar_contexts(regime, limit)
        return [
            MarketMemoryResponse(
                id=s["id"],
                symbol=s["symbol"],
                regime_type=s["regime_type"],
                volatility_metric=s["volatility_metric"],
                rsi_14=s["rsi_14"],
                funding_rate=s["funding_rate"]
            )
            for s in snaps
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve similar contexts: {e}")
