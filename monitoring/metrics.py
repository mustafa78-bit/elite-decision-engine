from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from core.kill_switch import KillSwitch

logger = logging.getLogger(__name__)


class MetricsService:

    def __init__(
        self,
        kill_switch: KillSwitch,
        ws_manager: Any,
        session_factory: Optional[Callable[[], Any]] = None,
    ) -> None:
        self._start_time = datetime.now(timezone.utc)
        self._request_count: int = 0
        self._kill_switch = kill_switch
        self._ws_manager = ws_manager
        self._session_factory = session_factory

    @property
    def uptime_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self._start_time).total_seconds()

    @property
    def request_count(self) -> int:
        return self._request_count

    def increment_requests(self) -> None:
        self._request_count += 1

    def _active_ws_clients(self) -> int:
        try:
            return self._ws_manager.active_count
        except Exception:
            return 0

    def _open_trades(self) -> int:
        if self._session_factory is None:
            return 0
        session = self._session_factory()
        try:
            from database import Trade
            return session.query(Trade).filter(Trade.status == "OPEN").count()
        except Exception:
            return 0
        finally:
            session.close()

    def snapshot(self) -> dict[str, Any]:
        return {
            "uptime_seconds": round(self.uptime_seconds, 2),
            "request_count": self.request_count,
            "active_ws_clients": self._active_ws_clients(),
            "open_trades": self._open_trades(),
            "engine_state": self._kill_switch.state().value,
        }
