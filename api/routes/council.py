from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from database import Signal, get_session
from execution.pipeline import TradingSignal

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_consensus_engine():
    from council.consensus import ConsensusEngine
    engine = ConsensusEngine()
    engine.register_defaults()
    return engine


@router.get("/council")
def get_council_status(request: Request):
    """Return the consensus engine status and registered agents."""
    try:
        engine = _get_consensus_engine()
        return {
            "agent_count": len(engine.agents),
            "agents": list(engine.agents.keys()),
            "weights": engine.weights,
            "stats": engine.stats,
        }
    except Exception as e:
        logger.error("Council status failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/council/evaluate/{signal_id}")
def council_evaluate_signal(signal_id: int, request: Request):
    """Evaluate a signal through the full AI Council (all 6 agents + consensus)."""
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        engine = _get_consensus_engine()
        report = engine.evaluate(signal=signal)

        return {
            "signal_id": signal_id,
            "symbol": report.symbol,
            "council_report": report.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Council evaluation failed for signal %s: %s", signal_id, e)
        return JSONResponse(status_code=500, content={"error": str(e), "signal_id": signal_id})
    finally:
        session.close()


@router.post("/council/evaluate")
def council_evaluate_direct(
    symbol: str,
    side: str = "LONG",
    timeframe: str = "1h",
    request: Request = None,
):
    """Evaluate a symbol directly through the AI Council without a DB signal."""
    try:
        from unittest.mock import MagicMock

        signal = MagicMock(spec=TradingSignal)
        signal.id = 0
        signal.symbol = symbol
        signal.side = side
        signal.timeframe = timeframe

        engine = _get_consensus_engine()
        report = engine.evaluate(signal=signal)

        return {
            "symbol": symbol,
            "side": side,
            "council_report": report.to_dict(),
        }
    except Exception as e:
        logger.error("Council direct evaluation failed for %s: %s", symbol, e)
        return JSONResponse(status_code=500, content={"error": str(e), "symbol": symbol})
