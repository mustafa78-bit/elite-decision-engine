from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionRequest:
    """Standardized input object for the Unified Decision Kernel."""

    symbol: str
    side: str
    timeframe: str = "1h"
    price: float = 0.0
    signals: list[str] = field(default_factory=list)
    strategy: str = "trend"
    metadata: dict[str, Any] = field(default_factory=dict)
