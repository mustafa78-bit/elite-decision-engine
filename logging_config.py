"""Centralized logging configuration for the Elite Decision Engine.

Usage:
    from logging_config import setup_logging
    setup_logging()

This configures three rotating file handlers and one console handler:

    engine.log     ← core.*, database, app
    trade.log      ← execution.*, scoring.*
    error.log      ← ERROR+ from all loggers

Call once at process start (e.g. in ``app.py:main()``).  Idempotent —
each call replaces all handlers on the root logger.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)-8s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 10 * 1024 * 1024
_BACKUP_COUNT = 5


class _ModuleFilter(logging.Filter):
    """Allow log records whose logger name starts with one of *prefixes*."""

    def __init__(self, prefixes):
        super().__init__()
        self.prefixes = prefixes

    def filter(self, record):
        return any(record.name.startswith(p) for p in self.prefixes)


def _file_handler(path, level, formatter, filter_=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    if filter_ is not None:
        handler.addFilter(filter_)
    return handler


def setup_logging(log_dir="logs"):
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    handlers = [
        console,
        _file_handler(
            os.path.join(log_dir, "engine.log"),
            logging.INFO,
            formatter,
            _ModuleFilter(("core", "database", "app")),
        ),
        _file_handler(
            os.path.join(log_dir, "trade.log"),
            logging.INFO,
            formatter,
            _ModuleFilter(("execution", "scoring")),
        ),
        _file_handler(
            os.path.join(log_dir, "error.log"),
            logging.ERROR,
            formatter,
        ),
    ]

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    for h in handlers:
        root.addHandler(h)
