"""OpportunityScanner — unified scanner that detects trade opportunities."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from market.services import MarketDataService
from scanner.confidence import ConfidenceScorer
from scanner.dto import ScannerDashboardDTO, opportunity_to_dto
from scanner.filters import FalseSignalFilter, MarketFilter
from scanner.models import Opportunity, ScanResult
from scanner.probability import ProbabilityEngine
from scanner.ranking import OpportunityRanker
from scanner.risk import RiskScorer
from scanner.strategies import (
    BreakoutStrategy,
    LiquidityStrategy,
    MomentumStrategy,
    ReversalStrategy,
    TrendStrategy,
)
from scanner.watchlist import WatchlistEngine

logger = logging.getLogger(__name__)

_DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


class OpportunityScanner:
    """Detect and rank trade opportunities across multiple symbols."""

    def __init__(
        self,
        market_service: Optional[MarketDataService] = None,
        ranker: Optional[OpportunityRanker] = None,
        symbols: Optional[list[str]] = None,
        probability_engine: Optional[ProbabilityEngine] = None,
        risk_scorer: Optional[RiskScorer] = None,
        confidence_scorer: Optional[ConfidenceScorer] = None,
        market_filter: Optional[MarketFilter] = None,
        false_signal_filter: Optional[FalseSignalFilter] = None,
        watchlist_engine: Optional[WatchlistEngine] = None,
    ) -> None:
        self.market_service = market_service or MarketDataService()
        self.ranker = ranker or OpportunityRanker()
        self.symbols = symbols or _DEFAULT_SYMBOLS

        self.trend = TrendStrategy()
        self.momentum = MomentumStrategy()
        self.breakout = BreakoutStrategy()
        self.reversal = ReversalStrategy()
        self.liquidity = LiquidityStrategy()

        self.probability = probability_engine or ProbabilityEngine()
        self.risk_scorer = risk_scorer or RiskScorer()
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()
        self.market_filter = market_filter or MarketFilter()
        self.false_signal_filter = false_signal_filter or FalseSignalFilter()
        self.watchlist = watchlist_engine or WatchlistEngine()

    def scan(
        self,
        symbols: Optional[list[str]] = None,
        timeframe: str = "1h",
        watchlist: Optional[str] = None,
    ) -> list[Opportunity]:
        """Scan symbols and return ranked opportunities."""
        target_symbols = symbols or self.symbols
        logger.info("Scanning %s symbols on %s", len(target_symbols), timeframe)

        results: list[ScanResult] = []
        for symbol in target_symbols:
            result = self._scan_symbol(symbol, timeframe)
            if result is not None:
                results.append(result)

        results = self._apply_filters(results)
        logger.info("Scan complete: %d results after filters", len(results))

        opportunities = self.ranker.rank(results)
        opportunities = self._enrich_opportunities(opportunities, results)

        if watchlist:
            opportunities = self.watchlist.filter_opportunities(opportunities, watchlist)

        return opportunities

    def get_opportunities_by_category(
        self,
        category: str,
        n: int = 5,
        timeframe: str = "1h",
        watchlist: str | None = None,
    ) -> list[Opportunity]:
        """Return top N opportunities for a given category.

        Categories:
            - "top-movers"         -> momentum strategy
            - "top-reversals"      -> reversal strategy
            - "top-breakouts"      -> breakout strategy
            - "top-trends"         -> trend strategy
            - "top-mean-reversions" -> reversal strategy (mean reversion)
        """
        strategy_map: dict[str, str] = {
            "top-movers": "momentum",
            "top-reversals": "reversal",
            "top-breakouts": "breakout",
            "top-trends": "trend",
            "top-mean-reversions": "reversal",
        }
        target_strategy = strategy_map.get(category)
        if target_strategy is None:
            return []

        opportunities = self.scan(timeframe=timeframe, watchlist=watchlist)
        filtered = [o for o in opportunities if o.strategy == target_strategy]
        return filtered[:n]

    @staticmethod
    def list_categories() -> list[dict[str, str]]:
        return [
            {"id": "top-movers", "label": "Top Movers", "description": "Strong momentum opportunities"},
            {"id": "top-reversals", "label": "Top Reversals", "description": "Reversal opportunities at extremes"},
            {"id": "top-breakouts", "label": "Top Breakouts", "description": "Price breakout with volume confirmation"},
            {"id": "top-trends", "label": "Top Trends", "description": "Trend-following opportunities"},
            {"id": "top-mean-reversions", "label": "Top Mean Reversions", "description": "Mean reversion opportunities"},
        ]

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

        intelligence = asset.intelligence
        ctx = asset.context

        return ScanResult(
            symbol=symbol,
            trend_score=trend_score,
            momentum_score=momentum_score,
            breakout_score=breakout_score,
            reversal_score=reversal_score,
            liquidity_score=liquidity_score,
            features=asset.features,
            signals=all_signals,
            intelligence={
                "fear_greed": intelligence.fear_greed if intelligence else {},
                "funding": intelligence.funding if intelligence else {},
                "liquidity_context": intelligence.liquidity_context if intelligence else {},
                "intelligence_confidence": intelligence.confidence if intelligence else 0.0,
            },
            market_session=ctx.get("session", ""),
            btc_trend=ctx.get("btc", {}).get("btc_trend", ""),
            fear_greed_label=intelligence.fear_greed.get("label", "") if intelligence else "",
            funding_level=ctx.get("funding", {}).get("state", ""),
        )

    def _apply_filters(self, results: list[ScanResult]) -> list[ScanResult]:
        filtered: list[ScanResult] = []
        for r in results:
            mf_reason = self._check_market_filter(r)
            if mf_reason:
                logger.debug("Market filter removed %s: %s", r.symbol, mf_reason)
                continue

            fs_reason = self._check_false_signal(r)
            if fs_reason:
                logger.debug("False signal filter removed %s: %s", r.symbol, fs_reason)
                continue

            filtered.append(r)
        return filtered

    def _check_market_filter(self, r: ScanResult) -> Optional[str]:
        should_filter, reason = self.market_filter.should_filter(
            r,
            btc_trend=r.btc_trend or None,
            market_session=r.market_session or None,
            fear_greed_label=r.fear_greed_label or None,
        )
        return reason if should_filter else None

    def _check_false_signal(self, r: ScanResult) -> Optional[str]:
        volume_score = r.intelligence.get("liquidity_context", {}).get("score")
        should_filter, reason = self.false_signal_filter.should_filter(r, volume_score=volume_score)
        return reason if should_filter else None

    def _enrich_opportunities(self, opportunities: list[Opportunity], results: list[ScanResult]) -> list[Opportunity]:
        result_map = {r.symbol: r for r in results}
        for opp in opportunities:
            r = result_map.get(opp.symbol)
            if r is None:
                continue

            prob, prob_signals = self.probability.estimate(
                composite_score=opp.score,
                trend_score=r.trend_score,
                momentum_score=r.momentum_score,
                breakout_score=r.breakout_score,
                reversal_score=r.reversal_score,
                liquidity_score=r.liquidity_score,
                btc_trend=r.btc_trend or None,
                funding_level=r.funding_level or None,
                fear_greed_value=self._parse_fear_greed(r),
            )
            opp.probability_score = prob
            opp.probability_signals = prob_signals

            risk, risk_signals = self.risk_scorer.score(
                volatility_class=r.features.get("volatility_class"),
                risk_feature=r.features.get("risk"),
                atr_pct=r.features.get("atr_pct"),
                liquidity_score=r.liquidity_score,
                reversal_score=r.reversal_score,
            )
            opp.risk_score = risk
            opp.risk_signals = risk_signals

            intel_conf = r.intelligence.get("intelligence_confidence", 0.0)
            conf, conf_signals = self.confidence_scorer.compute(
                probability=prob,
                risk_score=risk,
                intelligence_confidence=intel_conf,
                signal_count=len(r.signals),
            )
            opp.confidence = conf
            opp.confidence_signals = conf_signals

        return opportunities

    def top_opportunities(self, n: int = 5, timeframe: str = "1h") -> list[Opportunity]:
        """Return the top N opportunities from a full scan."""
        opportunities = self.scan(timeframe=timeframe)
        return opportunities[:n]

    def get_dashboard(self, n: int = 5, timeframe: str = "1h") -> ScannerDashboardDTO:
        """Return scanner dashboard data."""
        opportunities = self.scan(timeframe=timeframe)
        top = opportunities[:n]

        all_signals: list[str] = []
        for opp in top:
            all_signals.extend(opp.signals)

        from collections import Counter
        top_signals = [s for s, _ in Counter(all_signals).most_common(10)]

        btc_trends = [o.features.get("trend", "") for o in top if o.features]
        btc_context = self.market_service.get_context()
        fg = btc_context.get("funding", {})

        return ScannerDashboardDTO(
            symbols_scanned=len(top),
            opportunities_found=len(opportunities),
            top_opportunities=[opportunity_to_dto(o) for o in top],
            top_signals=top_signals,
            market_summary={
                "btc_trend": btc_context.get("btc", {}).get("btc_trend", "UNKNOWN"),
                "session": btc_context.get("session", ""),
                "funding_state": fg.get("state", "UNKNOWN"),
            },
            intelligence_summary={
                "avg_probability": round(sum(o.probability_score for o in top) / max(len(top), 1), 2),
                "avg_risk": round(sum(o.risk_score for o in top) / max(len(top), 1), 4),
                "avg_confidence": round(sum(o.confidence for o in top) / max(len(top), 1), 2),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _parse_fear_greed(r: ScanResult) -> Optional[float]:
        fg = r.intelligence.get("fear_greed", {})
        return fg.get("value") if fg else None
