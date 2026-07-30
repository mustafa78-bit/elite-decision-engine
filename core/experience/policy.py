import os
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ExperiencePolicy:
    """Governance Experience Policy.

    Manages configurable thresholds for evaluating Experience Sufficiency without hardcoded constants.
    """

    # Default thresholds
    MIN_EVENTS: int = int(os.getenv("EXPERIENCE_MIN_EVENTS", 5))
    MIN_HOURS: float = float(os.getenv("EXPERIENCE_MIN_HOURS", 24.0))

    _dynamic_overrides: Dict[str, Any] = {}

    @classmethod
    def get_min_events(cls) -> int:
        return cls._dynamic_overrides.get("MIN_EVENTS", cls.MIN_EVENTS)

    @classmethod
    def get_min_hours(cls) -> float:
        return cls._dynamic_overrides.get("MIN_HOURS", cls.MIN_HOURS)

    @classmethod
    def update_policy(cls, config: Dict[str, Any]) -> None:
        """Allow Governance to dynamically alter experience policy thresholds."""
        if "MIN_EVENTS" in config:
            cls._dynamic_overrides["MIN_EVENTS"] = int(config["MIN_EVENTS"])
            logger.info("Governance updated Experience MIN_EVENTS policy to %d", config["MIN_EVENTS"])
        if "MIN_HOURS" in config:
            cls._dynamic_overrides["MIN_HOURS"] = float(config["MIN_HOURS"])
            logger.info("Governance updated Experience MIN_HOURS policy to %.1f", config["MIN_HOURS"])


class GraduationPolicy:
    """Governance Graduation Policy.

    Manages configurable thresholds for evaluating Graduation Recommendations.
    """

    # Default thresholds
    WIN_RATE: float = float(os.getenv("GRADUATION_WIN_RATE", 0.55))
    PROFIT_FACTOR: float = float(os.getenv("GRADUATION_PROFIT_FACTOR", 1.2))
    MIN_TRADES: int = int(os.getenv("GRADUATION_MIN_TRADES", 5))

    _dynamic_overrides: Dict[str, Any] = {}

    @classmethod
    def get_win_rate(cls) -> float:
        return cls._dynamic_overrides.get("WIN_RATE", cls.WIN_RATE)

    @classmethod
    def get_profit_factor(cls) -> float:
        return cls._dynamic_overrides.get("PROFIT_FACTOR", cls.PROFIT_FACTOR)

    @classmethod
    def get_min_trades(cls) -> int:
        return cls._dynamic_overrides.get("MIN_TRADES", cls.MIN_TRADES)

    @classmethod
    def update_policy(cls, config: Dict[str, Any]) -> None:
        """Allow Governance to dynamically alter graduation policy thresholds."""
        if "WIN_RATE" in config:
            cls._dynamic_overrides["WIN_RATE"] = float(config["WIN_RATE"])
            logger.info("Governance updated Graduation WIN_RATE policy to %.2f", config["WIN_RATE"])
        if "PROFIT_FACTOR" in config:
            cls._dynamic_overrides["PROFIT_FACTOR"] = float(config["PROFIT_FACTOR"])
            logger.info("Governance updated Graduation PROFIT_FACTOR policy to %.2f", config["PROFIT_FACTOR"])
        if "MIN_TRADES" in config:
            cls._dynamic_overrides["MIN_TRADES"] = int(config["MIN_TRADES"])
            logger.info("Governance updated Graduation MIN_TRADES policy to %d", config["MIN_TRADES"])
