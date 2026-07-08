from __future__ import annotations

import logging
from typing import Optional, Type

from strategies.base import Strategy

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """Registry of available trading strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, Type[Strategy]] = {}

    def register(self, strategy_cls: Type[Strategy]) -> None:
        """Register a strategy class by its name attribute."""
        name = strategy_cls.name
        if name in self._strategies:
            logger.warning("Overwriting existing strategy: %s", name)
        self._strategies[name] = strategy_cls
        logger.info("Registered strategy: %s", name)

    def get(self, name: str) -> Optional[Type[Strategy]]:
        """Get a strategy class by name."""
        return self._strategies.get(name)

    def list(self) -> list[str]:
        """List all registered strategy names."""
        return list(self._strategies.keys())

    def instantiate(self, name: str) -> Optional[Strategy]:
        """Create an instance of a strategy by name."""
        cls = self.get(name)
        if cls is None:
            return None
        return cls()

    def count(self) -> int:
        return len(self._strategies)
