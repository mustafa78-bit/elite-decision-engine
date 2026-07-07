from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    manager: ConnectionManager = websocket.app.state.ws_manager
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    try:
        while True:
            text = await websocket.receive_text()
            _handle_incoming(client_id, text)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception:
        logger.exception("WebSocket error for client %s", client_id)
        manager.disconnect(client_id)


def _handle_incoming(client_id: str, text: str) -> None:
    try:
        data = json.loads(text)
        msg_type = data.get("type", "UNKNOWN")
        logger.debug("WebSocket message from %s: type=%s", client_id, msg_type)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON from client %s: %s", client_id, text[:100])
