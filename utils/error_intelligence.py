from __future__ import annotations

import logging
import traceback
from typing import Any, Optional
from fastapi import Request

logger = logging.getLogger(__name__)


def capture_exception(
    exc: Exception,
    module_name: str,
    request: Optional[Request] = None,
    severity: str = "MEDIUM",
    recoverable: bool = True,
) -> dict[str, Any]:
    """Capture and structure an exception for centralized Error Intelligence."""
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    stack_trace = "".join(tb)

    endpoint = "N/A"
    method = "N/A"
    query_params = {}
    headers = {}
    client_host = "N/A"

    if request is not None:
        endpoint = request.url.path
        method = request.method
        query_params = dict(request.query_params)
        headers = {k: v for k, v in request.headers.items() if k.lower() not in {"authorization", "cookie"}}
        if request.client:
            client_host = request.client.host

    structured_error = {
        "error_type": type(exc).__name__,
        "message": str(exc),
        "module": module_name,
        "endpoint": endpoint,
        "method": method,
        "query_params": query_params,
        "headers": headers,
        "client_host": client_host,
        "severity": severity,
        "recoverability": "RECOVERABLE" if recoverable else "FATAL",
        "stack_trace": stack_trace,
    }

    # Log as structured JSON or formatted block
    logger.error(
        "[Centralized Error Intelligence] Exception in %s on %s: %s (Severity: %s, Recoverability: %s)",
        module_name,
        endpoint,
        exc,
        severity,
        structured_error["recoverability"],
        extra={"structured_error": structured_error},
    )

    return structured_error
