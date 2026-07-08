import logging


logger = logging.getLogger(__name__)


class NotificationDispatcher:

    def emit(self, event, payload):
        logger.info(
            "Notification event: %s | payload=%s",
            event,
            payload,
        )

        return {
            "event": event,
            "payload": payload,
        }
