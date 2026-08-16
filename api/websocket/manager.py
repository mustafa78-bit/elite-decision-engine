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
        # Which user each connection belongs to -- populated at connect
        # time from the same JWT already validated to accept the
        # connection (mirrors api/middleware.py:57's request.state.user_id
        # extraction). Used by broadcast_to_owner() to scope user-owned
        # events (trades, notifications) to only that user's connections,
        # instead of api/websocket/manager.py's broadcast()'s global fan-out.
        self._client_user_ids: dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, room: str | None = None) -> None:
        if API_ENV == "development":
            await websocket.accept()
            self._clients.add(websocket)
            self._client_user_ids[websocket] = 1  # matches auth_middleware's dev-mode hardcode
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
        self._client_user_ids[websocket] = int(payload.get("sub", 0))
        if room:
            self._rooms.setdefault(room, set()).add(websocket)
        logger.info("WebSocket client connected (%d active, room=%s)", len(self._clients), room)

    async def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)
        self._client_user_ids.pop(websocket, None)
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

    async def broadcast_to_owner(self, message: str, owner_user_id: int | None) -> None:
        """Send `message` only to connections belonging to `owner_user_id`.

        Matches services/notification_service.py's `_owned_by()` NULL-
        fallback convention used for other user-scoped resources in this
        app: if `owner_user_id` is None (e.g. a background-job-created row
        with no specific owner, same rationale as Signal/Trade/
        Notification.user_id being nullable), falls back to broadcasting
        to every connected client rather than becoming invisible to
        everyone.
        """
        if owner_user_id is None:
            await self.broadcast(message)
            return

        stale: list[WebSocket] = []
        for ws in list(self._clients):
            if self._client_user_ids.get(ws) != owner_user_id:
                continue
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

    def connected_user_ids(self) -> set[int]:
        """Distinct user_ids with at least one active connection right now."""
        return set(self._client_user_ids.values())

    def client_count(self, room: str | None = None) -> int:
        if room:
            return len(self._rooms.get(room, set()))
        return len(self._clients)
