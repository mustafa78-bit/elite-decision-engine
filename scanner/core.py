"""OpportunityScanner — unified scanner that detects trade opportunities."""

from __future__ import annotations

import logging
from typing import Any, Optional

from market.services import MarketDataService
from scanner.models import Opportunity, ScanResult
from scanner.ranking import OpportunityRanker
from scanner.strategies import (
    BreakoutStrategy,
    LiquidityStrategy,
    MomentumStrategy,
    ReversalStrategy,
    TrendStrategy,
)

logger = logging.getLogger(__name__)

_DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


class OpportunityScanner:
    """Detect and rank trade opportunities across multiple symbols."""

    def __init__(
        self,
        market_service: Optional[MarketDataService] = None,
        ranker: Optional[OpportunityRanker] = None,
        symbols: Optional[list[str]] = None,
    ) -> None:
        self.market_service = market_service or MarketDataService()
        self.ranker = ranker or OpportunityRanker()
        self.symbols = symbols or _DEFAULT_SYMBOLS

        self.trend = TrendStrategy()
        self.momentum = MomentumStrategy()
        self.breakout = BreakoutStrategy()
        self.reversal = ReversalStrategy()
        self.liquidity = LiquidityStrategy()

    def scan(self, symbols: Optional[list[str]] = None, timeframe: str = "1h") -> list[Opportunity]:
        """Scan symbols and return ranked opportunities."""
        target_symbols = symbols or self.symbols
        logger.info("Scanning %s symbols on %s", len(target_symbols), timeframe)

        results: list[ScanResult] = []
        for symbol in target_symbols:
            result = self._scan_symbol(symbol, timeframe)
            if result is not None:
                results.append(result)

        logger.info("Scan complete: %d results, %d opportunities", len(results), len(results))
        return self.ranker.rank(results)

    def _scan_symbol(self, symbol: str, timeframe: str) -> Optional[ScanResult]:
        try:
            asset = self.market_service.get_asset(symbol, timeframe)
        except Exception as e:
            logger.warning("Failed to fetch asset %s: %s", symbol, e)
            return None

        if asset.is_empty:
            logger.debug("No data for %s, skipping", symbol)
            return None

        all_signals: list[str] = []

        trend_score, ts = self.trend.evaluate(asset)
        all_signals.extend(ts)

        momentum_score, ms = self.momentum.evaluate(asset)
        all_signals.extend(ms)

        breakout_score, bs = self.breakout.evaluate(asset)
        all_signals.extend(bs)

        reversal_score, rs = self.reversal.evaluate(asset)
        all_signals.extend(rs)

        liquidity_score, ls = self.liquidity.evaluate(asset)
        all_signals.extend(ls)

        return ScanResult(
            symbol=symbol,
            trend_score=trend_score,
            momentum_score=momentum_score,
            breakout_score=breakout_score,
            reversal_score=reversal_score,
            liquidity_score=liquidity_score,
            features=asset.features,
            signals=all_signals,
        )

    def top_opportunities(self, n: int = 5, timeframe: str = "1h") -> list[Opportunity]:
        """Return the top N opportunities from a full scan."""
        opportunities = self.scan(timeframe=timeframe)
        return opportunities[:n]
