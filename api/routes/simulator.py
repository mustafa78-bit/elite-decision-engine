from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from database import SimulationSession, SimulationTrade, get_session
from simulator.simulator_service import SimulatorService

logger = logging.getLogger(__name__)
router = APIRouter()

# Share a single stateful simulator service instance for in-memory session playback
_service = SimulatorService()


class SessionCreate(BaseModel):
    name: str = "Simulation Run"
    symbol: str = "BTC"
    timeframe: str = "1H"
    scenario_name: Optional[str] = "None"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    length: int = 100
    base_price: float = 50000.0


class TradeCreate(BaseModel):
    side: str  # LONG, SHORT
    entry_price: float
    quantity: float
    leverage: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class JumpRequest(BaseModel):
    target_date: str


class SpeedRequest(BaseModel):
    speed: float


def _serialize_session(s: SimulationSession) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "symbol": s.symbol,
        "timeframe": s.timeframe,
        "scenario_name": s.scenario_name,
        "start_date": s.start_date.isoformat() if s.start_date else None,
        "end_date": s.end_date.isoformat() if s.end_date else None,
        "current_index": s.current_index,
        "mode": s.mode,
        "initial_balance": s.initial_balance,
        "current_balance": s.current_balance,
        "metrics": s.metrics,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _serialize_trade(t: SimulationTrade) -> dict:
    return {
        "id": t.id,
        "session_id": t.session_id,
        "symbol": t.symbol,
        "side": t.side,
        "entry_price": t.entry_price,
        "exit_price": t.exit_price,
        "quantity": t.quantity,
        "leverage": t.leverage,
        "stop_loss": t.stop_loss,
        "take_profit": t.take_profit,
        "pnl": t.pnl,
        "status": t.status,
        "close_reason": t.close_reason,
        "elite_score": t.elite_score,
        "explain_data": t.explain_data,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "closed_at": t.closed_at.isoformat() if t.closed_at else None,
    }


# ─── Session Management ───────────────────────────────────────────────────


@router.post("/simulator/sessions")
def create_session(body: SessionCreate):
    session = get_session()
    try:
        start_dt = (
            datetime.fromisoformat(body.start_date)
            if body.start_date
            else datetime.now(timezone.utc) - timedelta(days=10)
        )
        end_dt = (
            datetime.fromisoformat(body.end_date)
            if body.end_date
            else datetime.now(timezone.utc)
        )

        # 1. Initialize stateful in-memory orchestrator
        _service.create_session(
            symbol=body.symbol.upper(),
            timeframe=body.timeframe,
            start_date=start_dt,
            end_date=end_dt,
            scenario_name=body.scenario_name,
            length=body.length,
            base_price=body.base_price,
        )

        # 2. Save session meta in DB
        db_session = SimulationSession(
            name=body.name,
            symbol=body.symbol.upper(),
            timeframe=body.timeframe,
            scenario_name=body.scenario_name,
            start_date=start_dt,
            end_date=end_dt,
            current_index=0,
            mode="MANUAL",
            initial_balance=100000.0,
            current_balance=100000.0,
            metrics={},
        )
        session.add(db_session)
        session.commit()
        session.refresh(db_session)

        return _serialize_session(db_session)
    except Exception as e:
        session.rollback()
        logger.error("Failed to create simulation session: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/simulator/sessions")
def list_sessions(limit: int = Query(50, ge=1, le=100)):
    session = get_session()
    try:
        rows = session.query(SimulationSession).order_by(SimulationSession.created_at.desc()).limit(limit).all()
        return [_serialize_session(r) for r in rows]
    finally:
        session.close()


@router.get("/simulator/sessions/{session_id}")
def get_session_details(session_id: int):
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        # Load session back into memory service if needed
        if not _service.replay_engine or _service.replay_engine.current_index != s.current_index:
            _service.create_session(
                symbol=s.symbol,
                timeframe=s.timeframe,
                start_date=s.start_date,
                end_date=s.end_date,
                scenario_name=s.scenario_name,
                length=100,
                base_price=s.initial_balance / 2,
            )
            _service.replay_engine.current_index = s.current_index

        return _serialize_session(s)
    finally:
        session.close()


@router.delete("/simulator/sessions/{session_id}")
def delete_session(session_id: int):
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        session.delete(s)
        session.commit()
        return {"status": "deleted"}
    except Exception as e:
        session.rollback()
        logger.error("Failed to delete session: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ─── Replay Controls ─────────────────────────────────────────────────────


@router.post("/simulator/sessions/{session_id}/step")
def step_session(session_id: int):
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        # Load into memory if empty
        self_load_memory(s)

        # Advance engine
        tick = _service.replay_engine.step()
        if tick:
            s.current_index = _service.replay_engine.current_index
            session.commit()

        # Update and auto-monitor any open trades at current price tick
        _monitor_sim_trades(session, s)

        return _service.get_current_state()
    finally:
        session.close()


@router.post("/simulator/sessions/{session_id}/play")
def play_session(session_id: int):
    s = load_and_verify_session(session_id)
    _service.replay_engine.start()
    return {"is_playing": True}


@router.post("/simulator/sessions/{session_id}/pause")
def pause_session(session_id: int):
    s = load_and_verify_session(session_id)
    _service.replay_engine.pause()
    return {"is_playing": False}


@router.post("/simulator/sessions/{session_id}/speed")
def speed_session(session_id: int, body: SpeedRequest):
    s = load_and_verify_session(session_id)
    _service.replay_engine.set_speed(body.speed)
    return {"speed": body.speed}


@router.post("/simulator/sessions/{session_id}/jump")
def jump_session(session_id: int, body: JumpRequest):
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        self_load_memory(s)
        target = datetime.fromisoformat(body.target_date)
        new_idx = _service.replay_engine.jump_to_date(target)
        s.current_index = new_idx
        session.commit()

        return _service.get_current_state()
    finally:
        session.close()


# ─── Simulated Execution & Trading ───────────────────────────────────────


@router.post("/simulator/sessions/{session_id}/trades")
def place_sim_trade(session_id: int, body: TradeCreate):
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        self_load_memory(s)
        tick = _service.replay_engine.current_tick
        if not tick:
            raise HTTPException(status_code=400, detail="Cannot place trade: no tick active")

        # Simulate execution with slippage, latency and fees using ExecutionSimulator
        fill = _service.execution_simulator.simulate_fill(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            symbol=s.symbol,
            side=body.side.upper(),
            quantity=Decimal(str(body.quantity)),
            price=Decimal(str(body.entry_price)),
        )

        explain_data = {
            "requested_price": float(fill.requested_price) if fill.requested_price else None,
            "fill_price": float(fill.fill_price),
            "slippage": float(fill.slippage),
            "fee": float(fill.fee),
            "latency_ms": fill.latency_ms,
            "partial": fill.partial,
            "council_confidence": 75.0,
        }

        trade = SimulationTrade(
            session_id=session_id,
            symbol=s.symbol,
            side=body.side.upper(),
            entry_price=float(fill.fill_price),
            quantity=float(fill.filled_quantity),
            leverage=body.leverage,
            stop_loss=body.stop_loss,
            take_profit=body.take_profit,
            status="OPEN",
            pnl=0.0,
            explain_data=explain_data,
        )
        session.add(trade)
        session.commit()
        session.refresh(trade)

        return _serialize_trade(trade)
    finally:
        session.close()


@router.get("/simulator/sessions/{session_id}/trades")
def list_sim_trades(session_id: int):
    session = get_session()
    try:
        trades = session.query(SimulationTrade).filter(SimulationTrade.session_id == session_id).all()
        return [_serialize_trade(t) for t in trades]
    finally:
        session.close()


@router.put("/simulator/sessions/{session_id}/trades/{trade_id}/close")
def close_sim_trade(session_id: int, trade_id: int):
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        self_load_memory(s)
        tick = _service.replay_engine.current_tick
        if not tick:
            raise HTTPException(status_code=400, detail="Cannot close trade: no tick active")

        trade = session.query(SimulationTrade).filter(
            SimulationTrade.session_id == session_id,
            SimulationTrade.id == trade_id,
        ).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")

        # Close trade at current tick price
        current_price = tick.candle.close
        pnl = (current_price - trade.entry_price) * trade.quantity * trade.leverage
        if trade.side.upper() == "SHORT":
            pnl = (trade.entry_price - current_price) * trade.quantity * trade.leverage

        trade.exit_price = current_price
        trade.pnl = round(pnl, 2)
        trade.status = "CLOSED"
        trade.close_reason = "MANUAL"
        trade.closed_at = datetime.now(timezone.utc)

        # Calculate institutional rating (0-100 Elite Score)
        trade.elite_score = _service.calculate_decision_score(
            confidence=trade.explain_data.get("council_confidence", 75.0),
            evidence_strength=70.0,
            risk_score=85.0 if (trade.leverage <= 5 and trade.stop_loss) else 50.0,
            pnl_pct=(trade.pnl / (trade.entry_price * trade.quantity)) * 100,
        )

        # Update balance
        s.current_balance = round(s.current_balance + pnl, 2)

        session.commit()
        return _serialize_trade(trade)
    finally:
        session.close()


# ─── Live Metrics & Training Report ──────────────────────────────────────


@router.get("/simulator/sessions/{session_id}/state")
def get_session_state(session_id: int):
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        self_load_memory(s)
        state = _service.get_current_state()
        if not state:
            raise HTTPException(status_code=400, detail="Cannot fetch state: replay uninitialized")

        # Overlay session balance
        state["initial_balance"] = s.initial_balance
        state["current_balance"] = s.current_balance
        return state
    finally:
        session.close()


@router.get("/simulator/sessions/{session_id}/report")
def get_training_report(session_id: int):
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        trades = session.query(SimulationTrade).filter(SimulationTrade.session_id == session_id).all()
        scorecard = _service.calculate_training_scorecard(trades)

        # Calculate final stats
        total_trades = len(trades)
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl < 0]
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0

        pnl_sum = sum(t.pnl for t in trades)

        return {
            "session_id": session_id,
            "symbol": s.symbol,
            "scenario": s.scenario_name,
            "timeframe": s.timeframe,
            "scorecard": scorecard,
            "statistics": {
                "total_trades": total_trades,
                "winning_trades": len(wins),
                "losing_trades": len(losses),
                "win_rate": round(win_rate, 2),
                "total_pnl": round(pnl_sum, 2),
                "initial_balance": s.initial_balance,
                "final_balance": s.current_balance,
            },
            "trades": [_serialize_trade(t) for t in trades],
        }
    finally:
        session.close()


@router.get("/simulator/sessions/{session_id}/export/json")
def export_session_json(session_id: int):
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")

        trades = session.query(SimulationTrade).filter(SimulationTrade.session_id == session_id).all()
        scorecard = _service.calculate_training_scorecard(trades)

        return {
            "export_version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "session": _serialize_session(s),
            "trades": [_serialize_trade(t) for t in trades],
            "scorecard": scorecard,
        }
    finally:
        session.close()


# ─── Helpers ─────────────────────────────────────────────────────────────


def self_load_memory(s: SimulationSession):
    """Restore simulation variables into stateless execution memory."""
    is_stale = False
    if _service.replay_engine:
        current_tick = _service.replay_engine.current_tick
        if current_tick:
            if current_tick.candle.symbol != s.symbol or _service.replay_engine.total_ticks != 100:
                is_stale = True
    if not _service.replay_engine or is_stale:
        _service.create_session(
            symbol=s.symbol,
            timeframe=s.timeframe,
            start_date=s.start_date,
            end_date=s.end_date,
            scenario_name=s.scenario_name,
            length=100,
            base_price=s.initial_balance / 2,
        )
    _service.replay_engine.current_index = s.current_index


def load_and_verify_session(session_id: int) -> SimulationSession:
    session = get_session()
    try:
        s = session.query(SimulationSession).filter(SimulationSession.id == session_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Session not found")
        self_load_memory(s)
        return s
    finally:
        session.close()


def _monitor_sim_trades(session: Any, s: SimulationSession):
    """Chronologically evaluate and trigger TP/SL exits for open simulator trades."""
    tick = _service.replay_engine.current_tick
    if not tick:
        return

    open_trades = session.query(SimulationTrade).filter(
        SimulationTrade.session_id == s.id,
        SimulationTrade.status == "OPEN",
    ).all()

    current_price = tick.candle.close

    for trade in open_trades:
        triggered = False
        reason = ""

        # Long TP/SL evaluation
        if trade.side.upper() == "LONG":
            if trade.take_profit and current_price >= trade.take_profit:
                triggered = True
                reason = "TP_HIT"
            elif trade.stop_loss and current_price <= trade.stop_loss:
                triggered = True
                reason = "SL_HIT"
        # Short TP/SL evaluation
        elif trade.side.upper() == "SHORT":
            if trade.take_profit and current_price <= trade.take_profit:
                triggered = True
                reason = "TP_HIT"
            elif trade.stop_loss and current_price >= trade.stop_loss:
                triggered = True
                reason = "SL_HIT"

        if triggered:
            exit_p = (
                trade.take_profit if reason == "TP_HIT" else trade.stop_loss
            ) or current_price
            pnl = (exit_p - trade.entry_price) * trade.quantity * trade.leverage
            if trade.side.upper() == "SHORT":
                pnl = (trade.entry_price - exit_p) * trade.quantity * trade.leverage

            trade.exit_price = exit_p
            trade.pnl = round(pnl, 2)
            trade.status = "CLOSED"
            trade.close_reason = reason
            trade.closed_at = datetime.now(timezone.utc)

            # Rating
            trade.elite_score = _service.calculate_decision_score(
                confidence=trade.explain_data.get("council_confidence", 75.0),
                evidence_strength=70.0,
                risk_score=90.0,
                pnl_pct=(trade.pnl / (trade.entry_price * trade.quantity)) * 100,
            )

            # Update session balance
            s.current_balance = round(s.current_balance + pnl, 2)

    session.commit()
