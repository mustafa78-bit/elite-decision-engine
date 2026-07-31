from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from simulator.models import (
    MissionReport,
    SessionMeta,
    SimStatus,
    SimulatorConfig,
    SimulatorState,
    SimulatedTrade,
    TrainingScore,
)

logger = logging.getLogger(__name__)

SESSIONS_DIR = Path("simulator/sessions")


class SessionManager:
    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._dir = storage_dir or SESSIONS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, SimulatorState] = {}
        self._active_id: Optional[str] = None

    @property
    def active_id(self) -> Optional[str]:
        return self._active_id

    @property
    def active(self) -> Optional[SimulatorState]:
        if self._active_id and self._active_id in self._sessions:
            return self._sessions[self._active_id]
        return None

    def create(self, config: SimulatorConfig, name: str = "") -> SimulatorState:
        sid = uuid.uuid4().hex[:12]
        state = SimulatorState(
            session_id=sid,
            config=config,
            portfolio_value=config.initial_capital,
            cash=config.initial_capital,
        )
        self._sessions[sid] = state
        self._active_id = sid
        meta = self._build_meta(state, name)
        self._save_meta(sid, meta)
        logger.info("Created simulator session %s", sid)
        return state

    def save(self, state: SimulatorState, name: str = "") -> None:
        self._sessions[state.session_id] = state
        path = self._dir / f"{state.session_id}.json"
        try:
            data = state.to_dict()
            data["candles"] = [c.to_dict() for c in state.candles]
            data["decisions"] = [d.to_dict() for d in state.decisions]
            data["trades"] = [t.to_dict() for t in state.trades]
            data["timeline"] = [e.to_dict() for e in state.timeline]
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            meta = self._build_meta(state, name)
            self._save_meta(state.session_id, meta)
            logger.info("Saved session %s", state.session_id)
        except Exception as e:
            logger.error("Failed to save session %s: %s", state.session_id, e)

    def load(self, session_id: str) -> Optional[SimulatorState]:
        if session_id in self._sessions:
            self._active_id = session_id
            return self._sessions[session_id]
        path = self._dir / f"{session_id}.json"
        if not path.exists():
            logger.warning("Session file not found: %s", path)
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            config = SimulatorConfig.from_dict(data.get("config", {}))
            state = SimulatorState(
                session_id=data["session_id"],
                status=SimStatus(data.get("status", "IDLE")),
                config=config,
                current_candle_index=data.get("current_candle_index", 0),
                total_candles=data.get("total_candles", 0),
                current_timestamp=data.get("current_timestamp"),
                current_price=data.get("current_price"),
                elapsed_seconds=data.get("elapsed_seconds", 0.0),
                portfolio_value=data.get("portfolio_value", config.initial_capital),
                cash=data.get("cash", config.initial_capital),
                open_positions=data.get("open_positions", 0),
                total_pnl=data.get("total_pnl", 0.0),
                win_count=data.get("win_count", 0),
                loss_count=data.get("loss_count", 0),
            )
            self._sessions[session_id] = state
            self._active_id = session_id
            logger.info("Loaded session %s", session_id)
            return state
        except Exception as e:
            logger.error("Failed to load session %s: %s", session_id, e)
            return None

    def delete(self, session_id: str) -> bool:
        path = self._dir / f"{session_id}.json"
        meta_path = self._dir / f"{session_id}.meta.json"
        try:
            if path.exists():
                path.unlink()
            if meta_path.exists():
                meta_path.unlink()
            self._sessions.pop(session_id, None)
            if self._active_id == session_id:
                self._active_id = None
            logger.info("Deleted session %s", session_id)
            return True
        except Exception as e:
            logger.error("Failed to delete session %s: %s", session_id, e)
            return False

    def list_sessions(self) -> list[SessionMeta]:
        metas: list[SessionMeta] = []
        for path in self._dir.glob("*.meta.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                config = SimulatorConfig.from_dict(data.get("config", {}))
                meta = SessionMeta(
                    id=data["id"],
                    name=data.get("name", ""),
                    created_at=data.get("created_at", ""),
                    updated_at=data.get("updated_at", ""),
                    config=config,
                    status=SimStatus(data.get("status", "IDLE")),
                    total_trades=data.get("total_trades", 0),
                    total_pnl=data.get("total_pnl", 0.0),
                    win_rate=data.get("win_rate", 0.0),
                )
                metas.append(meta)
            except Exception as e:
                logger.warning("Failed to load session meta %s: %s", path.name, e)
        metas.sort(key=lambda m: m.updated_at, reverse=True)
        return metas

    def compare_sessions(self, id_a: str, id_b: str) -> dict[str, Any]:
        a = self.load(id_a)
        b = self.load(id_b)
        if a is None or b is None:
            return {"error": "One or both sessions not found"}
        return {
            "session_a": {"id": id_a, "trades": len(a.trades), "pnl": a.total_pnl, "wins": a.win_count, "losses": a.loss_count},
            "session_b": {"id": id_b, "trades": len(b.trades), "pnl": b.total_pnl, "wins": b.win_count, "losses": b.loss_count},
            "differences": {
                "pnl_diff": round(b.total_pnl - a.total_pnl, 2),
                "trade_diff": len(b.trades) - len(a.trades),
            },
        }

    def _build_meta(self, state: SimulatorState, name: str = "") -> dict[str, Any]:
        trades = state.trades
        wins = sum(1 for t in trades if t.pnl > 0)
        total_wl = wins + sum(1 for t in trades if t.pnl < 0)
        return {
            "id": state.session_id,
            "name": name or f"Session {state.session_id[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "config": state.config.to_dict(),
            "status": state.status.value,
            "total_trades": len(trades),
            "total_pnl": state.total_pnl,
            "win_rate": round(wins / total_wl * 100, 2) if total_wl > 0 else 0.0,
        }

    def _save_meta(self, session_id: str, meta: dict[str, Any]) -> None:
        path = self._dir / f"{session_id}.meta.json"
        try:
            with open(path, "w") as f:
                json.dump(meta, f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save session meta %s: %s", session_id, e)
