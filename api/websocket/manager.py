from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: Optional[str] = None) -> None:
        await websocket.accept()
        self._clients.add(websocket)
        if room:
            self._rooms.setdefault(room, set()).add(websocket)
        logger.info("WebSocket client connected (%d active, room=%s)", len(self._clients), room)

    async def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)
        for room_clients in self._rooms.values():
            room_clients.discard(websocket)
        logger.info("WebSocket client disconnected (%d active)", len(self._clients))

    async def broadcast(self, message: str) -> None:
        stale: list[WebSocket] = []
        for ws in self._clients:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            await self.disconnect(ws)

    async def broadcast_to_room(self, room: str, message: str) -> None:
        clients = self._rooms.get(room, set())
        stale: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            await self.disconnect(ws)

    def client_count(self, room: Optional[str] = None) -> int:
        if room:
            return len(self._rooms.get(room, set()))
        return len(self._clients)
