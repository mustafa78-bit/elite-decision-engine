import logging
from typing import Set

from fastapi import WebSocket


logger = logging.getLogger(__name__)


class WebSocketManager:

    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)
        logger.info("WebSocket client connected (%d active)", len(self._clients))

    async def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)
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
