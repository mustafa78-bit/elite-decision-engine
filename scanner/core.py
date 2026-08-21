"""OpportunityScanner — unified scanner that detects trade opportunities."""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from config import (
    FIXED_COIN_UNIVERSE,
    SCAN_MAX_WORKERS,
    SCANNER_FUNDING_CROWDING_PENALTY,
    SCANNER_MTF_PENALTY,
)
from execution.tp_sl import TPSLEngine
from market.services import MarketDataService
from market_data.mtf import MTFEngine
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

if TYPE_CHECKING:
    from services.temporary_watch_service import TemporaryWatchService

logger = logging.getLogger(__name__)

_DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# Funding levels that mean "the crowd is already positioned this way" for a
# given side -- mirrors council/macro_agent.py's FUNDING_RISK_MAP vocabulary
# (interpret_funding_risk() in market_data/funding/models.py is the shared
# source of both), applied here as a scanner-side score penalty rather than
# a hard filter: crowded doesn't mean wrong, just higher squeeze risk.
_CROWDED_LONG_FUNDING_LEVELS = frozenset({"extreme", "high", "elevated"})
_CROWDED_SHORT_FUNDING_LEVELS = frozenset({"extreme_negative", "high_negative", "elevated_negative"})

# scan() had no cache at all -- every one of get_opportunities_by_category(),
# top_opportunities(), and get_dashboard() called it fresh, and each of
# THOSE is hit independently by the frontend (Scanner page's category tabs,
# CommandDeck's opportunities panel, the dashboard endpoint) plus the
# periodic background scan loop. Confirmed live 2026-08-21: a single
# /scanner/category/top-movers request took 36.8s end to end, and 5
# concurrent full 25-symbol scans were observed firing within 172ms of each
# other -- every caller doing its own uncoordinated full scan. Same
# class-level TTL-cache + thundering-herd-lock pattern already applied
# today to MultiProvider.get_ohlcv() and FundingCollector's methods.
_SCAN_CACHE_TTL_SECONDS = 30.0


class OpportunityScanner:
    """Detect and rank trade opportunities across multiple symbols."""

    def __init__(
        self,
        market_service: MarketDataService | None = None,
        ranker: OpportunityRanker | None = None,
        symbols: list[str] | None = None,
        probability_engine: ProbabilityEngine | None = None,
        risk_scorer: RiskScorer | None = None,
        confidence_scorer: ConfidenceScorer | None = None,
        market_filter: MarketFilter | None = None,
        false_signal_filter: FalseSignalFilter | None = None,
        watchlist_engine: WatchlistEngine | None = None,
        temporary_watch_service: TemporaryWatchService | None = None,
        tp_sl_engine: TPSLEngine | None = None,
        mtf_engine: MTFEngine | None = None,
    ) -> None:
        self.market_service = market_service or MarketDataService()
        self.ranker = ranker or OpportunityRanker()
        if symbols is not None:
            self.symbols = symbols
        else:
            from services.temporary_watch_service import TemporaryWatchService
            temp_watch = temporary_watch_service or TemporaryWatchService()
            # Fixed permanent universe (founder's chosen 25) plus whatever
            # temporary watches are currently active, deduplicated. Replaces
            # the old dynamic top-100-by-volume universe -- that was ~100
            # symbols x several external calls each (OHLCV, funding, OI,
            # whale, news) per scan cycle, the real cause of observed
            # Hyperliquid/NVIDIA 429s.
            try:
                active = temp_watch.active_symbols()
            except Exception as e:
                # A DB hiccup (or, on a genuinely fresh deployment, the
                # temporary_watches table not existing yet -- the real
                # uvicorn entrypoint never calls database.create_tables())
                # must not crash scanner construction: OpportunityScanner()
                # is default-constructed synchronously by several unguarded
                # call sites (api/routes/scanner.py, services/terminal_
                # service.py, decision/aggregator.py), so an unhandled
                # exception here would take down the whole Scanner/Terminal
                # API surface, not just the temporary-watch feature.
                logger.warning(
                    "Failed to load active temporary watches, falling back to "
                    "FIXED_COIN_UNIVERSE only: %s", e,
                )
                active = []
            self.symbols = list(dict.fromkeys([*FIXED_COIN_UNIVERSE, *active]))

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
        self.tp_sl_engine = tp_sl_engine or TPSLEngine()
        self.mtf_engine = mtf_engine or MTFEngine()

        self._scan_cache: dict[tuple[Any, ...], tuple[float, list[Opportunity]]] = {}
        self._scan_cache_lock = threading.Lock()

    def scan(
        self,
        symbols: list[str] | None = None,
        timeframe: str = "1h",
        watchlist: str | None = None,
    ) -> list[Opportunity]:
        """Scan symbols and return ranked opportunities."""
        target_symbols = symbols or self.symbols
        cache_key = (tuple(target_symbols), timeframe, watchlist)

        now = time.monotonic()
        cached = self._scan_cache.get(cache_key)
        if cached is not None and now - cached[0] < _SCAN_CACHE_TTL_SECONDS:
            return cached[1]

        with self._scan_cache_lock:
            cached = self._scan_cache.get(cache_key)
            if cached is not None and now - cached[0] < _SCAN_CACHE_TTL_SECONDS:
                return cached[1]
            opportunities = self._scan_uncached(target_symbols, timeframe, watchlist)
            self._scan_cache[cache_key] = (now, opportunities)
            return opportunities

    def _scan_uncached(
        self,
        target_symbols: list[str],
        timeframe: str,
        watchlist: str | None,
    ) -> list[Opportunity]:
        logger.info("Scanning %s symbols on %s", len(target_symbols), timeframe)

        # Per-symbol enrichment (news/whale/funding/OI, some LLM-backed via
        # NewsService.classify_and_score()) was observed live taking 26-56s
        # each under real NVIDIA load -- fully sequential across ~25 symbols
        # turned a scan into 31-33 minutes against SCAN_INTERVAL_SECONDS=900,
        # silently defeating that cadence. Bounded thread pool instead: the
        # strategy evaluators are stateless and the shared caches/rate-
        # limiters (IntelligenceService, WhaleService, FundingCollector/
        # OpenInterestCollector) are already lock-protected class-level
        # singletons built for concurrent access, so this doesn't bypass
        # throttling -- it lets independent symbols' I/O overlap instead of
        # queuing one at a time. See config.SCAN_MAX_WORKERS.
        with ThreadPoolExecutor(max_workers=SCAN_MAX_WORKERS) as executor:
            scanned = executor.map(lambda s: self._scan_symbol(s, timeframe), target_symbols)
            results: list[ScanResult] = [r for r in scanned if r is not None]

        results = self._apply_filters(results)
        logger.info("Scan complete: %d results after filters", len(results))

        opportunities = self.ranker.rank(results)

        result_map = {r.symbol: r for r in results}
        side_filtered: list[Opportunity] = []
        for opp in opportunities:
            r = result_map.get(opp.symbol)
            if r is None:
                side_filtered.append(opp)
                continue
            should_filter, reason = self.market_filter.should_filter(
                r,
                side=opp.side,
                btc_trend=r.btc_trend or None,
                fear_greed_label=r.fear_greed_label or None,
            )
            if should_filter:
                logger.debug("Market filter removed opportunity %s (side=%s): %s", opp.symbol, opp.side, reason)
                continue
            side_filtered.append(opp)
        opportunities = side_filtered

        opportunities = self._enrich_opportunities(opportunities, results)

        # _enrich_opportunities() can shrink score/confidence (MTF
        # disagreement, funding crowding) after ranker.rank() already sorted
        # by the pre-enrichment score -- re-sort so the final order reflects
        # what actually got returned.
        opportunities.sort(key=lambda o: o.score, reverse=True)
        for i, opp in enumerate(opportunities):
            opp.rank = i + 1

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

    def _scan_symbol(self, symbol: str, timeframe: str) -> ScanResult | None:
        # Two-phase: a cheap technical-only pass first (OHLCV + indicators,
        # no NVIDIA/whale/funding/OI/fear-greed fan-out), then only pay for
        # the expensive intelligence enrichment when at least one directional
        # strategy actually found something. A symbol with zero signal on
        # every directional strategy was never going to become a real
        # opportunity regardless of what its news sentiment says -- this
        # keeps today's 25-symbol universe's behavior unchanged in practice
        # (most symbols do show some signal) while being the piece that
        # makes a much larger universe (the founder's planned 125/625 scale-
        # up) viable: NVIDIA call volume scales with how many symbols show
        # real technical interest, not with the size of the universe itself.
        try:
            asset = self.market_service.get_asset(symbol, timeframe, enrich_intelligence=False)
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

        if max(trend_score, momentum_score, breakout_score, reversal_score) > 0:
            # IntelligenceService.enrich() mutates and returns the same
            # Asset object -- don't rebind `asset` to its return value here,
            # a mocked market_service (common in tests) would otherwise
            # silently replace the real test-provided asset with an
            # unconfigured MagicMock.
            self.market_service.intelligence.enrich(asset)

        intelligence = asset.intelligence
        ctx = asset.context

        return ScanResult(
            symbol=symbol,
            price=asset.price,
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
                "open_interest": intelligence.open_interest if intelligence else {},
                "news": intelligence.news if intelligence else [],
                "whales": intelligence.whales if intelligence else [],
            },
            market_session=ctx.get("session", ""),
            btc_trend=ctx.get("btc", {}).get("btc_trend", ""),
            fear_greed_label=intelligence.fear_greed.get("label", "") if intelligence else "",
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

    def _check_market_filter(self, r: ScanResult) -> str | None:
        should_filter, reason = self.market_filter.should_filter(
            r,
            market_session=r.market_session or None,
        )
        return reason if should_filter else None

    def _check_false_signal(self, r: ScanResult) -> str | None:
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
                fear_greed_value=self._parse_fear_greed(r),
                side=opp.side,
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

            opp.trend_score = r.trend_score

            # Same ATR-multiplier formula a real trade gets (execution/
            # tp_sl.py), so a scanner opportunity's suggested levels are
            # consistent with what actually happens if it's traded, not a
            # separate/inconsistent estimate. features["atr_pct"] is a
            # percentage (market/features/store.py) -- convert back to a
            # raw price-unit ATR using this opportunity's own price.
            if opp.price > 0:
                atr_pct = r.features.get("atr_pct") or 0.0
                atr = (atr_pct / 100.0) * opp.price
                try:
                    levels = self.tp_sl_engine.calculate(entry=opp.price, atr=atr, side=opp.side)
                    opp.stop = levels["stop"]
                    opp.tp1 = levels["tp1"]
                    opp.tp2 = levels["tp2"]
                except ValueError:
                    pass

            funding_data = r.intelligence.get("funding", {})
            opp.funding_score = funding_data.get("risk_score", 0.0) if funding_data else 0.0

            oi_data = r.intelligence.get("open_interest", {})
            opp.oi_score = oi_data.get("strength", 0.0) if oi_data else 0.0

            news_articles = r.intelligence.get("news", [])
            if news_articles:
                from market.intelligence.news import NewsService
                sentiment = NewsService().sentiment_score(news_articles)
                opp.cvd_score = (sentiment + 1.0) / 2.0
            else:
                opp.cvd_score = 0.0

            # MTF confirmation: shrink score/confidence when the higher
            # timeframes disagree with this opportunity's side. Only applied
            # here (already-ranked, typically small opportunity list), not
            # per scanned symbol -- MTFEngine.score() makes 3 real OHLCV
            # calls (15m/1h/4h) per invocation.
            try:
                mtf_score = self.mtf_engine.score(opp.symbol, opp.side)
            except Exception as e:
                logger.warning("MTF confirmation failed for %s: %s", opp.symbol, e)
                mtf_score = 1.0
            mtf_multiplier = 1.0 - SCANNER_MTF_PENALTY * (1.0 - mtf_score)
            if mtf_score < 1.0:
                opp.signals.append("MTF_PARTIAL_CONFIRMATION" if mtf_score > 0 else "MTF_CONTRADICTS_SIDE")
            opp.score = round(opp.score * mtf_multiplier, 4)
            opp.confidence = round(opp.confidence * mtf_multiplier, 4)

            # Funding-crowding penalty: an opportunity whose side matches the
            # crowd already leaning that way (extreme funding) carries real
            # squeeze risk beyond what the technical score alone reflects.
            crowded = (
                (opp.side == "LONG" and funding_data.get("level") in _CROWDED_LONG_FUNDING_LEVELS)
                or (opp.side == "SHORT" and funding_data.get("level") in _CROWDED_SHORT_FUNDING_LEVELS)
            )
            if crowded:
                opp.signals.append("CROWDED_FUNDING_RISK")
                funding_multiplier = 1.0 - SCANNER_FUNDING_CROWDING_PENALTY
                opp.score = round(opp.score * funding_multiplier, 4)
                opp.confidence = round(opp.confidence * funding_multiplier, 4)

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
            timestamp=datetime.now(UTC).isoformat(),
        )

    @staticmethod
    def _parse_fear_greed(r: ScanResult) -> float | None:
        fg = r.intelligence.get("fear_greed", {})
        return fg.get("value") if fg else None
