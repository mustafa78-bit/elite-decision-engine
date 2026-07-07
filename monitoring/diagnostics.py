from __future__ import annotations

import logging
import sys
from typing import Any, Callable, Optional


logger = logging.getLogger(__name__)


class DiagnosticsService:

    def __init__(
        self,
        session_factory: Optional[Callable[[], Any]] = None,
    ) -> None:
        self._session_factory = session_factory

    def _check_database(self) -> bool:
        if self._session_factory is None:
            return False
        session = self._session_factory()
        try:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            session.close()

    def runtime_summary(self) -> dict[str, Any]:
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "database_connected": self._check_database(),
            "api_status": "running",
        }
