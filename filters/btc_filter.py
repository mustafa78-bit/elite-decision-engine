from __future__ import annotations

import logging
from typing import Any

from market_data.btc_health import BTCHealth

logger = logging.getLogger(__name__)


class BTCHealthFilter:
    def __init__(self, btc_health: BTCHealth | None = None):
        self.btc_health = btc_health or BTCHealth()

    def is_healthy(self) -> bool:
        try:
            score = self.btc_health.score()
            return score >= 0.30
        except Exception as exc:
            logger.warning("BTC health score check failed in is_healthy: %s", exc)
            return True

    def evaluate(self, data: Any = None, side: str = "LONG") -> dict[str, Any]:
        side_upper = side.upper() if side else "LONG"
        if side_upper == "SHORT":
            return {
                "ok": True,
                "score": 1.0,
                "reason": "SHORT signals are not restricted by BTC health"
            }

        try:
            score = self.btc_health.score()
            if score < 0.30:
                return {
                    "ok": False,
                    "score": score,
                    "reason": f"BTC health score {score} is below threshold 0.30"
                }
            return {
                "ok": True,
                "score": score,
                "reason": f"BTC health score {score} is healthy"
            }
        except Exception as exc:
            logger.warning("BTC health score check failed in evaluate: %s", exc)
            return {
                "ok": True,
                "score": 1.0,
                "reason": f"BTC health check error fallback (passed): {exc}"
            }
