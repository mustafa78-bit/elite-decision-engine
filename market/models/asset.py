from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from market.intelligence.models import IntelligenceBundle


@dataclass
class AssetMetadata:
    symbol: str
    base_asset: str = ""
    quote_asset: str = "USDT"
    exchange: str = "hyperliquid"
    asset_type: str = "spot"
    decimals: int = 8
    min_size: float = 0.001


@dataclass
class Asset:
    """Unified asset model — the single representation of any traded asset.

    All market data, indicators, features, and context converge here.
    Future modules (Scanner, News, Whale, AI) will enrich this model.
    """

    symbol: str
    metadata: AssetMetadata

    price: float = 0.0
    ohlcv: Optional[pd.DataFrame] = None
    indicators: dict[str, Any] = field(default_factory=dict)
    features: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    news: list[dict[str, Any]] = field(default_factory=list)
    whales: list[dict[str, Any]] = field(default_factory=list)
    intelligence: Optional[IntelligenceBundle] = None

    timestamp: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, symbol: str, price: float = 0.0) -> Asset:
        return cls(
            symbol=symbol,
            metadata=AssetMetadata(symbol=symbol),
            price=price,
        )

    @property
    def is_empty(self) -> bool:
        if self.price > 0:
            return False
        if self.ohlcv is not None:
            return self.ohlcv.empty
        return True
