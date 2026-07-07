from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas import TradeItem, TradesResponse

_CLOSED_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})

router = APIRouter(tags=["trades"])


@router.get("/trades", response_model=TradesResponse)
async def get_trades(request: Request) -> TradesResponse:
    session = request.app.state.session_factory()
    try:
        from database import Trade

        open_trades = (
            session.query(Trade).filter(Trade.status == "OPEN").all()
        )
        closed_trades = (
            session.query(Trade)
            .filter(Trade.status.in_(_CLOSED_STATUSES))
            .all()
        )
    finally:
        session.close()

    return TradesResponse(
        open=[_to_item(t) for t in open_trades],
        closed=[_to_item(t) for t in closed_trades],
    )


def _to_item(trade: object) -> TradeItem:
    return TradeItem(
        id=int(getattr(trade, "id", 0)),
        symbol=str(getattr(trade, "symbol", "")),
        side=str(getattr(trade, "side", "")),
        entry=float(getattr(trade, "entry", 0.0)),
        pnl=float(getattr(trade, "pnl", 0.0)),
        status=str(getattr(trade, "status", "")),
        close_reason=(
            str(getattr(trade, "close_reason", None))
            if getattr(trade, "close_reason", None) is not None
            else None
        ),
        exit_price=(
            float(getattr(trade, "exit_price", None))
            if getattr(trade, "exit_price", None) is not None
            else None
        ),
    )
