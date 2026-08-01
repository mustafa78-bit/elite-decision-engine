from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    signal: str  # LONG, SHORT, or NEUTRAL
    confidence: float = 0.0
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class Strategy(ABC):
    """Abstract base for all trading strategies."""

    name: str = "base"

    @abstractmethod
    def evaluate(self, symbol: str, market_data: Any) -> Optional[StrategyResult]:
        ...

    @abstractmethod
    def description(self) -> str:
        ...
