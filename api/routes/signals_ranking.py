from fastapi import APIRouter, Query

from database import Signal, get_session

router = APIRouter()


def _decision(confidence: float) -> str:
    if confidence >= 90:
        return "STRONG_APPROVE"
    if confidence >= 80:
        return "APPROVE"
    if confidence >= 70:
        return "WATCH"
    return "REJECT"


@router.get("/signals/ranking")
def get_signals_ranking(limit: int = Query(50, ge=1, le=200)):
    session = get_session()
    try:
        rows = (
            session.query(Signal)
            .order_by(Signal.score.desc().nullslast())
            .limit(limit)
            .all()
        )
    finally:
        session.close()

    return [
        {
            "rank": i + 1,
            "id": s.id,
            "symbol": s.symbol,
            "side": s.side,
            "timeframe": s.timeframe,
            "score": round(s.score, 3) if s.score is not None else 0,
            "confidence": round(s.confidence, 2) if s.confidence is not None else 0,
            "decision": _decision(s.confidence or 0),
            "trend_score": round(s.trend_score, 2) if s.trend_score is not None else 0,
            "volume_score": round(s.volume_score, 2) if s.volume_score is not None else 0,
            "btc_score": round(s.btc_health, 2) if s.btc_health is not None else 0,
            "risk_score": round(s.risk_score, 2) if s.risk_score is not None else 0,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for i, s in enumerate(rows)
    ]
