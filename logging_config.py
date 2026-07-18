"""Centralized logging configuration for the Elite Decision Engine.

Usage:
    from logging_config import setup_logging
    setup_logging()

This configures three rotating file handlers and one console handler:

    engine.log     ← core.*, database, app
    trade.log      ← execution.*, scoring.*
    error.log      ← ERROR+ from all loggers

In production (API_ENV=production), console output uses JSON format
for structured log ingestion.
"""

import json
import logging
import os
import re
from logging.handlers import RotatingFileHandler

from config import LOG_LEVEL

LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)-8s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 10 * 1024 * 1024
_BACKUP_COUNT = 5

_SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(password|passwd|secret|token|key|api[_-]?key)\s*[:=]\s*["\']?[^\s,;\'"]+'), r'\1=***'),
    (re.compile(r'(?i)(Authorization:\s*Bearer\s+)\S+'), r'\1***'),
    (re.compile(r'(?i)(jwt[_-]?secret)\s*=\s*["\']?[^\s,;\'"]+'), r'\1=***'),
    (re.compile(r'(?i)(encryption[_-]?key)\s*=\s*["\']?[^\s,;\'"]+'), r'\1=***'),
]


class _SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            for pattern, replacement in _SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        if record.args:
            cleaned = []
            for arg in record.args:
                s = str(arg)
                for pattern, replacement in _SENSITIVE_PATTERNS:
                    s = pattern.sub(replacement, s)
                cleaned.append(s)
            record.args = tuple(cleaned)
        return True


class _ModuleFilter(logging.Filter):
    def __init__(self, prefixes):
        super().__init__()
        self.prefixes = prefixes

    def filter(self, record):
        return any(record.name.startswith(p) for p in self.prefixes)


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        })


def _file_handler(path, level, formatter, filter_=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    if filter_ is not None:
        handler.addFilter(filter_)
    return handler


def setup_logging(log_dir="logs"):
    api_env = os.getenv("API_ENV", "development")
    is_prod = api_env == "production"

    level = getattr(logging, LOG_LEVEL, logging.INFO)

    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_formatter = _JsonFormatter() if is_prod else logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    sensitive_filter = _SensitiveDataFilter()

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(console_formatter)
    console.addFilter(sensitive_filter)

    handlers = [
        console,
        _file_handler(
            os.path.join(log_dir, "engine.log"),
            logging.INFO,
            file_formatter,
            _ModuleFilter(("core", "database", "app")),
        ),
        _file_handler(
            os.path.join(log_dir, "trade.log"),
            logging.INFO,
            file_formatter,
            _ModuleFilter(("execution", "scoring")),
        ),
        _file_handler(
            os.path.join(log_dir, "error.log"),
            logging.ERROR,
            file_formatter,
        ),
    ]

    for h in handlers:
        h.addFilter(sensitive_filter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    for h in handlers:
        root.addHandler(h)


def log_state(logger_name: str, component: str, state: str, **extra) -> None:
    logger = logging.getLogger(logger_name)
    parts = [f"component={component}", f"state={state}"]
    parts.extend(f"{k}={v}" for k, v in extra.items())
    logger.info(" | ".join(parts))
