"""IntelligenceService — orchestrates all intelligence sources for an Asset."""

from __future__ import annotations

import logging
from typing import Any, Optional

from market.features import FeatureStore
from market.intelligence.exchange_flow import ExchangeFlowService
from market.intelligence.fear_greed import FearGreedService
from market.intelligence.liquidity import LiquidityContextAnalyzer
from market.intelligence.models import IntelligenceBundle
from market.intelligence.news import NewsService
from market.intelligence.whale import WhaleService
from market.models import Asset
from market_data.funding.collector import FundingCollector
from market_data.funding.models import interpret_funding_risk
from market_data.open_interest.collector import OpenInterestCollector
from market_data.open_interest.models import detect_oi_trend

logger = logging.getLogger(__name__)


class IntelligenceService:
    """Aggregate all intelligence sources into a unified bundle per symbol."""

    def __init__(
        self,
        funding_collector: Optional[FundingCollector] = None,
        oi_collector: Optional[OpenInterestCollector] = None,
        fear_greed: Optional[FearGreedService] = None,
        news: Optional[NewsService] = None,
        whale: Optional[WhaleService] = None,
        exchange_flow: Optional[ExchangeFlowService] = None,
        liquidity: Optional[LiquidityContextAnalyzer] = None,
    ) -> None:
        self.funding_collector = funding_collector or FundingCollector()
        self.oi_collector = oi_collector or OpenInterestCollector()
        self.fear_greed = fear_greed or FearGreedService()
        self.news = news or NewsService()
        self.whale = whale or WhaleService()
        self.exchange_flow = exchange_flow or ExchangeFlowService()
        self.liquidity = liquidity or LiquidityContextAnalyzer()

    def enrich(self, asset: Asset) -> Asset:
        """Enrich an Asset with full intelligence data."""
        if asset.is_empty:
            return asset

        symbol = asset.symbol
        indicators = asset.indicators
        features = asset.features
        price = asset.price

        funding_data = self._get_funding(symbol)
        oi_data = self._get_open_interest(symbol)
        btc_ctx = asset.context.get("btc", {})
        session = asset.context.get("session", "")

        rsi = indicators.get("rsi")
        vol_score = indicators.get("volatility_score")
        volume_score = indicators.get("volume_score")
        atr = indicators.get("atr")

        fg = self.fear_greed.compute(
            rsi=rsi,
            btc_trend=btc_ctx.get("btc_trend"),
            volatility_score=vol_score,
            funding_rate=funding_data.get("annualized_rate") if funding_data else None,
        )

        news_data = self.news.analyze(
            symbol=symbol,
            price=price,
            price_change_24h=self._estimate_24h_change(asset),
            btc_trend=btc_ctx.get("btc_trend"),
        )

        whale_data = self.whale.detect(
            symbol=symbol,
            volume_score=volume_score,
            volatility_score=vol_score,
            price=price,
        )

        flow = self.exchange_flow.analyze(
            symbol=symbol,
            volume_score=volume_score,
            volatility_score=vol_score,
            trend=features.get("trend"),
        )

        liq = self.liquidity.analyze(
            symbol=symbol,
            volume_score=volume_score,
            liquidity=features.get("liquidity"),
            atr=atr,
            price=price,
        )

        bundle = IntelligenceBundle(
            symbol=symbol,
            funding=funding_data or {},
            open_interest=oi_data or {},
            btc_context=btc_ctx,
            fear_greed=fg,
            news=news_data,
            whales=whale_data,
            market_session=session,
            exchange_flow=flow,
            liquidity_context=liq,
        )

        asset.intelligence = bundle
        return asset

    def _get_funding(self, symbol: str) -> Optional[dict[str, Any]]:
        try:
            rate = self.funding_collector.fetch_for_symbol(symbol)
            if rate is not None:
                risk = interpret_funding_risk(rate)
                return {
                    "rate": rate.rate,
                    "annualized_rate": rate.annualized_rate,
                    "risk_score": risk.get("risk_score", 0.0),
                    "level": risk.get("level", "NEUTRAL"),
                }
        except Exception as e:
            logger.debug("Funding unavailable for %s: %s", symbol, e)
        return None

    def _get_open_interest(self, symbol: str) -> Optional[dict[str, Any]]:
        try:
            oi_data = self.oi_collector.fetch_with_trend(symbol)
            if oi_data.get("value", 0) > 0:
                return oi_data
        except Exception as e:
            logger.debug("OI unavailable for %s: %s", symbol, e)
        return None

    @staticmethod
    def _estimate_24h_change(asset: Asset) -> Optional[float]:
        ohlcv = asset.ohlcv
        if ohlcv is not None and len(ohlcv) >= 24:
            price_now = float(ohlcv["close"].iloc[-1])
            price_24h = float(ohlcv["close"].iloc[-24])
            if price_24h > 0:
                return round((price_now - price_24h) / price_24h * 100, 2)
        return None
