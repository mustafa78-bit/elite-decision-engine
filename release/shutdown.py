from __future__ import annotations

import logging
from typing import Any, Optional

from database import engine

logger = logging.getLogger(__name__)


class GracefulShutdown:

    def __init__(
        self,
        ws_manager: Optional[Any] = None,
    ) -> None:
        self._ws_manager = ws_manager

    def shutdown(self) -> dict[str, Any]:
        results: dict[str, Any] = {}

        results["database"] = self._close_database()
        results["websocket_clients"] = self._disconnect_websockets()
        results["background_tasks"] = self._cancel_background_tasks()

        return results

    def _close_database(self) -> str:
        try:
            engine.dispose()
            logger.info("Database engine disposed")
            return "closed"
        except Exception as e:
            logger.error("Failed to dispose database engine: %s", e)
            return f"error: {e}"

    def _disconnect_websockets(self) -> str:
        if self._ws_manager is None:
            return "no_manager"
        try:
            count = self._ws_manager.active_count
            self._ws_manager.disconnect_all()
            logger.info("Disconnected %s WebSocket clients", count)
            return f"disconnected_{count}"
        except Exception as e:
            logger.error("Failed to disconnect WebSocket clients: %s", e)
            return f"error: {e}"

    def _cancel_background_tasks(self) -> str:
        return "noop"
