from __future__ import annotations

import logging
from typing import Optional

from fastapi import WebSocket

from auth.jwt import decode_access_token
from config import API_ENV

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str | None = None) -> None:
        if API_ENV == "development":
            await websocket.accept()
            self._clients.add(websocket)
            if room:
                self._rooms.setdefault(room, set()).add(websocket)
            logger.info("WebSocket client connected (dev mode, %d active, room=%s)", len(self._clients), room)
            return
        token = websocket.query_params.get("token", "")
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        payload = decode_access_token(token)
        if payload is None:
            await websocket.close(code=4001, reason="Invalid or expired token")
            return
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
        # Iterate a snapshot -- a client connecting mid-broadcast (a real,
        # concurrent possibility since each `await ws.send_text` yields
        # control back to the event loop) would otherwise mutate `_clients`
        # while this loop is iterating it, raising "Set changed size during
        # iteration" and aborting delivery to the remaining clients.
        stale: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            await self.disconnect(ws)

    async def broadcast_to_room(self, room: str, message: str) -> None:
        clients = self._rooms.get(room, set())
        stale: list[WebSocket] = []
        for ws in list(clients):
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            await self.disconnect(ws)

    def client_count(self, room: str | None = None) -> int:
        if room:
            return len(self._rooms.get(room, set()))
        return len(self._clients)
