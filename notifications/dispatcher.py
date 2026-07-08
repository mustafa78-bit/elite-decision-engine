import asyncio
import logging
from typing import Optional

from api.websocket.manager import WebSocketManager
from notifications.serializer import serialize_event


logger = logging.getLogger(__name__)


class NotificationDispatcher:

    def __init__(self, websocket_manager: Optional[WebSocketManager] = None) -> None:
        self.websocket_manager = websocket_manager

    def emit(self, event, payload):
        logger.info(
            "Notification event: %s | payload=%s",
            event,
            payload,
        )

        message = serialize_event(event, payload)

        if self.websocket_manager is not None:
            self._broadcast(message)

        return {
            "event": event,
            "payload": payload,
        }

    def _broadcast(self, message: str) -> None:
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.ensure_future(
                    self.websocket_manager.broadcast(message)
                )
        except RuntimeError:
            pass
