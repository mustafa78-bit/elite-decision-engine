from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from sqlalchemy import text

import config as config_module

logger = logging.getLogger(__name__)


class StartupValidator:

    def __init__(
        self,
        session_factory: Optional[Callable[[], Any]] = None,
        ws_manager: Optional[Any] = None,
        monitoring_service: Optional[Any] = None,
    ) -> None:
        self._session_factory = session_factory
        self._ws_manager = ws_manager
        self._monitoring_service = monitoring_service

    def _check_config(self) -> tuple[bool, Optional[str]]:
        mandatory = [
            "CHECK_INTERVAL", "MIN_SCORE", "MAX_OPEN_TRADES",
            "MAX_EXPOSURE_PER_SYMBOL", "MAX_PORTFOLIO_EXPOSURE",
            "MAX_DAILY_LOSS", "MAX_POSITION_SIZE_USD", "ACCOUNT_EQUITY",
            "RISK_PER_TRADE_PERCENT", "ATR_MULTIPLIER", "MIN_POSITION_QUANTITY",
            "DRY_RUN",
        ]
        missing = [key for key in mandatory if not hasattr(config_module, key)]
        if missing:
            return False, f"Missing config: {', '.join(missing)}"
        return True, None

    def _check_database(self) -> tuple[bool, Optional[str]]:
        if self._session_factory is None:
            return False, "No session_factory configured"
        session = self._session_factory()
        try:
            session.execute(text("SELECT 1"))
            return True, None
        except Exception as e:
            return False, f"Database connection failed: {e}"
        finally:
            session.close()

    def _check_api(self) -> tuple[bool, Optional[str]]:
        return True, None

    def _check_websocket(self) -> tuple[bool, Optional[str]]:
        if self._ws_manager is None:
            return False, "WebSocket manager not configured"
        return True, None

    def _check_monitoring(self) -> tuple[bool, Optional[str]]:
        if self._monitoring_service is None:
            return False, "Monitoring service not configured"
        return True, None

    def validate(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        all_pass = True

        for name in ("config", "database", "api", "websocket", "monitoring"):
            check = getattr(self, f"_check_{name}")()
            ok, err = check
            results[name] = {"ok": ok}
            if err:
                results[name]["error"] = err
            if not ok:
                all_pass = False

        results["all_pass"] = all_pass
        return results
