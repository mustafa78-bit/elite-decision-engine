from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response

from api.websocket.manager import WebSocketManager
from simulator.models import (
    AIDecisionMode,
    ScenarioType,
    SimSpeed,
    SimStatus,
    SimulatorConfig,
    SimulatorState,
)
from simulator.replay_engine import MarketReplayEngine
from simulator.report_generator import ReportGenerator
from simulator.scenarios import SCENARIOS, generate_scenario_data
from simulator.session_manager import SessionManager
from simulator.simulator_engine import SimulatorEngine

logger = logging.getLogger(__name__)

router = APIRouter()

_engine: SimulatorEngine | None = None
_session_mgr: SessionManager | None = None
_ws_manager: WebSocketManager | None = None
_replay_engine: MarketReplayEngine | None = None


async def _ws_broadcast_state(state: SimulatorState) -> None:
    try:
        await _get_ws().broadcast_to_room("simulator", json.dumps({
            "event": "SIMULATOR_STATE",
            "timestamp": state.current_timestamp or 0,
            "payload": state.to_dict(),
        }))
    except Exception:
        pass


async def _ws_broadcast_trade(trade: Any) -> None:
    try:
        await _get_ws().broadcast_to_room("simulator", json.dumps({
            "event": "SIMULATOR_TRADE",
            "payload": trade.to_dict() if hasattr(trade, "to_dict") else trade,
        }))
    except Exception:
        pass


async def _ws_broadcast_decision(decision: Any) -> None:
    try:
        await _get_ws().broadcast_to_room("simulator", json.dumps({
            "event": "SIMULATOR_DECISION",
            "payload": decision.to_dict() if hasattr(decision, "to_dict") else decision,
        }))
    except Exception:
        pass


async def _ws_broadcast_candle(candle: Any) -> None:
    try:
        await _get_ws().broadcast_to_room("simulator", json.dumps({
            "event": "SIMULATOR_CANDLE",
            "payload": candle.to_dict() if hasattr(candle, "to_dict") else candle,
        }))
    except Exception:
        pass


def _get_engine() -> SimulatorEngine:
    global _engine
    if _engine is None:
        from council.consensus import ConsensusEngine

        council_engine = ConsensusEngine()
        council_engine.register_defaults()
        _engine = SimulatorEngine(
            replay_engine=MarketReplayEngine(),
            report_generator=ReportGenerator(),
            council_engine=council_engine,
        )
        # Registered once against the module-level singleton engine, not per
        # /ws/simulator connection -- broadcast_to_room() already fans out to
        # every socket in the room from a single registration, and these
        # listener lists have no unsubscribe API, so registering per-connect
        # leaked 4 more closures on every reconnect.
        _engine.on_state(lambda s: asyncio.ensure_future(_ws_broadcast_state(s)))
        _engine.on_trade(lambda t: asyncio.ensure_future(_ws_broadcast_trade(t)))
        _engine.on_decision(lambda d: asyncio.ensure_future(_ws_broadcast_decision(d)))
        _engine.on_candle(lambda c: asyncio.ensure_future(_ws_broadcast_candle(c)))
    return _engine


def _get_session_mgr() -> SessionManager:
    global _session_mgr
    if _session_mgr is None:
        _session_mgr = SessionManager()
    return _session_mgr


def _get_ws() -> WebSocketManager:
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager


def _init_engine_from_state(state: SimulatorState) -> SimulatorEngine:
    eng = _get_engine()
    eng._replay = MarketReplayEngine()
    eng._replay._candles = list(state.candles)
    eng._replay._index = state.current_candle_index
    eng._replay._symbol = state.config.symbol
    eng._state = state
    return eng


# ── Session CRUD ────────────────────────────────────────────────────────────


@router.get("/simulator/sessions")
def list_sessions():
    mgr = _get_session_mgr()
    sessions = mgr.list_sessions()
    return {"sessions": [s.to_dict() for s in sessions]}


@router.post("/simulator/sessions")
def create_session(config: SimulatorConfig, name: str = ""):
    mgr = _get_session_mgr()
    state = mgr.create(config, name=name)
    return {"session_id": state.session_id, "state": state.to_dict()}


@router.get("/simulator/sessions/{session_id}")
def get_session(session_id: str):
    mgr = _get_session_mgr()
    state = mgr.load(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return state.to_dict()


@router.delete("/simulator/sessions/{session_id}")
def delete_session(session_id: str):
    mgr = _get_session_mgr()
    ok = mgr.delete(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


@router.post("/simulator/sessions/{session_id}/save")
def save_session(session_id: str, name: str = ""):
    eng = _get_engine()
    if eng.state is None or eng.state.session_id != session_id:
        state = _get_session_mgr().load(session_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Session not found")
        _init_engine_from_state(state)
    _get_session_mgr().save(eng.state, name=name)
    return {"saved": True}


@router.get("/simulator/sessions/compare/{id_a}/{id_b}")
def compare_sessions(id_a: str, id_b: str):
    mgr = _get_session_mgr()
    result = mgr.compare_sessions(id_a, id_b)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Simulation Control ──────────────────────────────────────────────────────


@router.post("/simulator/start")
async def start_simulation(config: SimulatorConfig, name: str = ""):
    eng = _get_engine()
    if eng.running:
        raise HTTPException(status_code=409, detail="Simulation already running")
    sid = await eng.start(config, name=name)
    if eng.state:
        _get_session_mgr().save(eng.state, name=name)
    return {"session_id": sid, "state": eng.state.to_dict() if eng.state else {}}


@router.post("/simulator/pause")
def pause_simulation():
    eng = _get_engine()
    if not eng.state or eng.state.status != SimStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Simulation not running")
    eng.pause()
    return {"status": "PAUSED"}


@router.post("/simulator/resume")
def resume_simulation():
    eng = _get_engine()
    if not eng.state or eng.state.status != SimStatus.PAUSED:
        raise HTTPException(status_code=409, detail="Simulation not paused")
    eng.resume()
    return {"status": "RESUMED"}


@router.post("/simulator/stop")
def stop_simulation():
    eng = _get_engine()
    if eng.state is None:
        raise HTTPException(status_code=409, detail="No active simulation")
    state = eng.stop()
    if state:
        _get_session_mgr().save(state)
    return {"status": "STOPPED", "state": state.to_dict() if state else {}}


@router.post("/simulator/reset")
def reset_simulation():
    eng = _get_engine()
    eng.reset()
    return {"status": "RESET"}


@router.post("/simulator/step")
def step_simulation():
    eng = _get_engine()
    candle = eng.step_candle()
    if candle is None:
        raise HTTPException(status_code=409, detail="Cannot step - simulation not paused or no more data")
    return {"candle": candle.to_dict(), "state": eng.state.to_dict() if eng.state else {}}


@router.get("/simulator/state")
def get_simulator_state():
    eng = _get_engine()
    if eng.state is None:
        return {"status": "IDLE", "state": None}
    return eng.state.to_dict()


@router.post("/simulator/speed")
def set_speed(speed: SimSpeed):
    eng = _get_engine()
    if eng.state is None:
        raise HTTPException(status_code=409, detail="No active simulation")
    eng.state.config.speed = speed
    return {"speed": speed.value}


@router.post("/simulator/seek")
def seek_to_timestamp(timestamp: int):
    eng = _get_engine()
    ok = eng.seek_to(timestamp)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid timestamp")
    return {"state": eng.state.to_dict() if eng.state else {}}


# ── Trading ──────────────────────────────────────────────────────────────────


@router.post("/simulator/trade")
def manual_trade(
    side: str = Query(pattern="^(BUY|SELL|LONG|SHORT)$"),
    entry_price: float = Query(gt=0),
    stop_loss: float = Query(gt=0),
    take_profit: float = Query(gt=0),
    quantity: float = Query(gt=0),
    leverage: float = Query(1.0, ge=1, le=100),
    trailing_stop: float | None = Query(None, gt=0),
):
    eng = _get_engine()
    if eng.state is None:
        raise HTTPException(status_code=409, detail="No active simulation")
    norm_side = "LONG" if side in ("BUY", "LONG") else "SHORT"
    trade = eng.execute_manual_trade(norm_side, entry_price, stop_loss, take_profit, quantity, leverage, trailing_stop)
    if trade is None:
        raise HTTPException(status_code=400, detail="Failed to create trade")
    return {"trade": trade.to_dict()}


@router.post("/simulator/trade/{trade_id}/close")
def close_trade(trade_id: str, exit_price: float | None = Query(None, gt=0)):
    eng = _get_engine()
    ok = eng.close_trade(trade_id, exit_price)
    if not ok:
        raise HTTPException(status_code=404, detail="Trade not found or already closed")
    return {"closed": True}


@router.post("/simulator/trades/close-all")
def close_all_trades(exit_price: float | None = Query(None, gt=0)):
    eng = _get_engine()
    closed = eng.close_all_trades(exit_price)
    return {"closed_count": closed}


# ── Reports ──────────────────────────────────────────────────────────────────


@router.get("/simulator/report")
def get_report():
    eng = _get_engine()
    report = eng.get_report()
    if report is None:
        raise HTTPException(status_code=409, detail="No active simulation")
    return report.to_dict()


@router.get("/simulator/report/json")
def export_report_json():
    eng = _get_engine()
    data = eng.get_report_json()
    if not data:
        raise HTTPException(status_code=409, detail="No active simulation")
    return Response(content=data, media_type="application/json")


@router.get("/simulator/report/pdf")
def export_report_pdf():
    eng = _get_engine()
    pdf = eng.get_report_pdf()
    if not pdf:
        raise HTTPException(status_code=409, detail="No active simulation")
    return Response(content=pdf, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="mission_report_{eng.state.session_id}.pdf"',
    })


# ── Scenarios ────────────────────────────────────────────────────────────────


@router.get("/simulator/scenarios")
def list_scenarios():
    return {
        "scenarios": {
            k.value: {
                "name": v["name"],
                "description": v["description"],
            }
            for k, v in SCENARIOS.items()
        }
    }


@router.post("/simulator/scenarios/generate")
def generate_scenario(
    scenario_type: ScenarioType,
    symbol: str = "BTC",
    timeframe: str = "1h",
    num_candles: int = 200,
    start_price: float | None = None,
):
    df = generate_scenario_data(scenario_type, symbol, timeframe, num_candles, start_price)
    if df is None or df.empty:
        raise HTTPException(status_code=500, detail="Failed to generate scenario data")
    candles = []
    for _, row in df.iterrows():
        candles.append({
            "timestamp": int(row.get("timestamp", 0)),
            "open": float(row.get("open", 0)),
            "high": float(row.get("high", 0)),
            "low": float(row.get("low", 0)),
            "close": float(row.get("close", 0)),
            "volume": float(row.get("volume", 0)),
        })
    return {
        "scenario": scenario_type.value,
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "count": len(candles),
    }


# ── Status ───────────────────────────────────────────────────────────────────


@router.get("/simulator/status")
def simulator_status():
    eng = _get_engine()
    return {
        "active": eng.state is not None,
        "running": eng.running,
        "status": eng.state.status.value if eng.state else "IDLE",
        "session_id": eng.state.session_id if eng.state else None,
        "progress": eng._replay.progress if hasattr(eng, "_replay") else 0.0,
        "current_candle": eng._replay.index if hasattr(eng, "_replay") else 0,
        "total_candles": eng._replay.total if hasattr(eng, "_replay") else 0,
        "current_price": eng.state.current_price if eng.state else None,
        "regime": eng.state.regime.value if eng.state else "UNKNOWN",
        "trades": len(eng.state.trades) if eng.state else 0,
        "open_positions": eng.state.open_positions if eng.state else 0,
        "total_pnl": eng.state.total_pnl if eng.state else 0.0,
        "portfolio_value": eng.state.portfolio_value if eng.state else 0.0,
        "founder_mode": eng.state.config.founder_mode if eng.state else False,
        "founder_metrics": eng.state.founder_metrics if eng.state else None,
    }


# ── WebSocket ────────────────────────────────────────────────────────────────


@router.websocket("/ws/simulator")
async def ws_simulator(websocket: WebSocket):
    ws = _get_ws()
    await ws.connect(websocket, room="simulator")
    eng = _get_engine()

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                cmd = msg.get("command", "")
                if cmd == "get_state":
                    if eng.state:
                        await websocket.send_text(json.dumps({
                            "event": "SIMULATOR_STATE",
                            "payload": eng.state.to_dict(),
                        }))
                elif cmd == "ping":
                    await websocket.send_text(json.dumps({"event": "PONG"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ws.disconnect(websocket)
    except Exception:
        await ws.disconnect(websocket)
        raise
