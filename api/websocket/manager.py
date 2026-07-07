from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket


logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self._connections[client_id] = websocket
        logger.info("WebSocket client connected: %s", client_id)

    def disconnect(self, client_id: str) -> None:
        self._connections.pop(client_id, None)
        logger.info("WebSocket client disconnected: %s", client_id)

    async def broadcast(self, event: dict[str, Any]) -> None:
        disconnected: list[str] = []
        for client_id, ws in self._connections.items():
            try:
                await ws.send_json(event)
            except Exception:
                logger.warning("Failed to send to client %s — removing", client_id)
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect(client_id)

    async def send_to(self, client_id: str, event: dict[str, Any]) -> bool:
        ws = self._connections.get(client_id)
        if ws is None:
            return False
        try:
            await ws.send_json(event)
            return True
        except Exception:
            logger.warning("Failed to send to client %s — removing", client_id)
            self.disconnect(client_id)
            return False

    def disconnect_all(self) -> None:
        for client_id in list(self._connections.keys()):
            self.disconnect(client_id)

    @property
    def active_count(self) -> int:
        return len(self._connections)

    @property
    def active_clients(self) -> list[str]:
        return list(self._connections.keys())
