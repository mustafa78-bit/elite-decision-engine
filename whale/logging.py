import logging
from typing import Optional


class WhaleLogger:

    def __init__(self, name: str = "whale_intelligence"):
        self.logger = logging.getLogger(name)
        self._setup_handler()

    def _setup_handler(self) -> None:
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(name)s] %(levelname)s: %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def whale_event(self, event_type: str, details: Optional[dict] = None) -> None:
        self.logger.info(f"WHALE_EVENT: {event_type} | {details or ''}")
