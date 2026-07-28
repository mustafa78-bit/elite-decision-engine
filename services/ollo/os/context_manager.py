from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Patterns for extracting context from user queries
COIN_PATTERN = re.compile(r"\b(BTC|ETH|SOL|XRP|ADA|DOT|DOGE|AVAX|LINK|LTC|NEAR|UNI|ICP)\b", re.IGNORECASE)
TIMEFRAME_PATTERN = re.compile(r"\b(1m|5m|15m|1h|4h|1d|1w)\b", re.IGNORECASE)
STRATEGY_PATTERN = re.compile(r"\b(ema_cross|mean_reversion|momentum|breakout|scalping|grid)\b", re.IGNORECASE)


class ContextManager:
    """Manages persistent session context to enable zero-repetition continuous conversations."""

    _instance: Optional[ContextManager] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._context: Dict[str, Any] = {
            "current_coin": "BTC",
            "current_timeframe": "1h",
            "current_strategy": "ema_cross",
            "current_portfolio": "default",
            "current_discussion": "general",
        }
        self._initialized = True

    def get(self, key: str, default: Any = None) -> Any:
        """Get an active context value."""
        return self._context.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a context value."""
        self._context[key] = value
        logger.info("Context updated: %s = %s", key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert full context state to a dictionary."""
        return dict(self._context)

    def clear(self) -> None:
        """Reset context to default states."""
        self._context = {
            "current_coin": "BTC",
            "current_timeframe": "1h",
            "current_strategy": "ema_cross",
            "current_portfolio": "default",
            "current_discussion": "general",
        }
        logger.info("Session context cleared to defaults.")

    def update_from_query(self, query: str) -> None:
        """Analyze a user query and dynamically extract and persist conversational context."""
        if not query:
            return

        # 1. Extract Coin
        coin_match = COIN_PATTERN.search(query)
        if coin_match:
            coin = coin_match.group(1).upper()
            self.set("current_coin", coin)

        # 2. Extract Timeframe
        tf_match = TIMEFRAME_PATTERN.search(query)
        if tf_match:
            tf = tf_match.group(1).lower()
            self.set("current_timeframe", tf)

        # 3. Extract Strategy
        strat_match = STRATEGY_PATTERN.search(query)
        if strat_match:
            strat = strat_match.group(1).lower()
            self.set("current_strategy", strat)


# Global singleton instance
context_manager = ContextManager()
