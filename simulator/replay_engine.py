from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timeframe": self.timeframe,
        }


@dataclass
class NewsEvent:
    id: str
    timestamp: datetime
    headline: str
    content: str
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    impact: str  # HIGH, MEDIUM, LOW

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "headline": self.headline,
            "content": self.content,
            "sentiment": self.sentiment,
            "impact": self.impact,
        }


@dataclass
class WhaleEvent:
    id: str
    timestamp: datetime
    event_type: str  # LARGE_BUY, LARGE_SELL, LIQUIDATION, FUNDING_SHIFT, OI_SPIKE, CEX_INFLOW, DEX_INFLOW
    size: float
    value_usd: float
    price: float
    details: str
    funding_rate: Optional[float] = None
    open_interest: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "size": self.size,
            "value_usd": self.value_usd,
            "price": self.price,
            "details": self.details,
            "funding_rate": self.funding_rate,
            "open_interest": self.open_interest,
        }


@dataclass
class RegimeState:
    timestamp: datetime
    regime: str  # BULL, BEAR, SIDEWAYS, VOLATILE
    risk_mode: str  # RISK_ON, RISK_OFF
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "regime": self.regime,
            "risk_mode": self.risk_mode,
            "description": self.description,
        }


@dataclass
class ReplayTick:
    """A synchronized chronological slice of the market state."""
    timestamp: datetime
    candle: Candle
    news: List[NewsEvent] = field(default_factory=list)
    whales: List[WhaleEvent] = field(default_factory=list)
    regime: Optional[RegimeState] = None
    alerts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "candle": self.candle.to_dict(),
            "news": [n.to_dict() for n in self.news],
            "whales": [w.to_dict() for w in self.whales],
            "regime": self.regime.to_dict() if self.regime else None,
            "alerts": self.alerts,
        }


class ScenarioGenerator:
    """Generates high-fidelity synthetic scenario data for institutional testing."""

    @staticmethod
    def generate(
        scenario_name: str,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        length: int = 100,
        base_price: float = 50000.0,
    ) -> List[ReplayTick]:
        random.seed(hash(scenario_name + symbol) & 0xFFFFFFFF)
        ticks: List[ReplayTick] = []
        current_price = base_price
        current_time = start_date

        # Interval mapping
        td_map = {"1m": 1, "5m": 5, "15m": 15, "1H": 60, "4H": 240, "1D": 1440}
        interval_minutes = td_map.get(timeframe, 60)

        # Base market variables
        volatility = 0.002  # base standard deviation per candle
        funding_rate = 0.0001
        open_interest = 50000000.0  # $50M base

        for i in range(length):
            # Apply scenario dynamics
            bias = 0.0
            volume_multiplier = 1.0
            whales_in_tick: List[WhaleEvent] = []
            news_in_tick: List[NewsEvent] = []
            regime = "SIDEWAYS"
            risk_mode = "RISK_OFF"

            # ── Scenario Modeling ──
            if scenario_name.upper() == "FLASH_CRASH":
                if 20 <= i <= 25:
                    bias = -0.06  # Catastrophic dump
                    volume_multiplier = 10.0
                    volatility = 0.02
                    regime = "VOLATILE"
                    risk_mode = "RISK_OFF"
                    if i == 21:
                        news_in_tick.append(NewsEvent(
                            id=f"news_fc_{i}",
                            timestamp=current_time,
                            headline="LEVERAGE LIQUIDATIONS CASCADE THROUGH ORDERBOOKS",
                            content="A sudden spike in liquidations triggered massive cascading market sells across major perpetual venues.",
                            sentiment="BEARISH",
                            impact="HIGH"
                        ))
                    whales_in_tick.append(WhaleEvent(
                        id=f"whale_fc_{i}",
                        timestamp=current_time,
                        event_type="LIQUIDATION",
                        size=float(random.randint(100, 500)),
                        value_usd=current_price * 200,
                        price=current_price,
                        details="Cascading leveraged liquidations hit hyperliquid engine",
                        funding_rate=funding_rate,
                        open_interest=open_interest * 0.8
                    ))
                    open_interest *= 0.95
                elif 26 <= i <= 35:
                    bias = 0.015  # Partial fast recovery
                    volume_multiplier = 4.0
                    volatility = 0.01
                    regime = "VOLATILE"
                    whales_in_tick.append(WhaleEvent(
                        id=f"whale_fc_buy_{i}",
                        timestamp=current_time,
                        event_type="LARGE_BUY",
                        size=float(random.randint(50, 150)),
                        value_usd=current_price * 100,
                        price=current_price,
                        details="Whale bidding the crash dev",
                    ))
                else:
                    bias = 0.0002
                    volatility = 0.0015
                    regime = "SIDEWAYS"

            elif scenario_name.upper() == "BULL_RUN":
                bias = 0.004  # steady appreciation
                volume_multiplier = 1.5 + (i * 0.01)
                volatility = 0.003
                funding_rate = 0.0003 + (i * 0.00001)
                open_interest *= 1.005
                regime = "BULL"
                risk_mode = "RISK_ON"
                if i % 15 == 0:
                    news_in_tick.append(NewsEvent(
                        id=f"news_br_{i}",
                        timestamp=current_time,
                        headline=f"CAPITAL INFLOWS INTO {symbol} REACH RECORD HIGHS",
                        content="Institutional and retail spot volumes confirm strong sustained demand.",
                        sentiment="BULLISH",
                        impact="MEDIUM"
                    ))
                if i % 8 == 0:
                    whales_in_tick.append(WhaleEvent(
                        id=f"whale_br_{i}",
                        timestamp=current_time,
                        event_type="LARGE_BUY",
                        size=float(random.randint(200, 1000)),
                        value_usd=current_price * 500,
                        price=current_price,
                        details="Continuous accumulation on spot orderbook",
                        funding_rate=funding_rate,
                        open_interest=open_interest
                    ))

            elif scenario_name.upper() == "CAPITULATION":
                if i < 40:
                    bias = -0.002
                    regime = "BEAR"
                elif 40 <= i <= 50:
                    bias = -0.018  # Final capitulation flush
                    volume_multiplier = 8.0
                    volatility = 0.012
                    regime = "VOLATILE"
                    whales_in_tick.append(WhaleEvent(
                        id=f"whale_cap_{i}",
                        timestamp=current_time,
                        event_type="LIQUIDATION",
                        size=float(random.randint(500, 2000)),
                        value_usd=current_price * 1000,
                        price=current_price,
                        details="Forced capitulation liquidations of long positions",
                    ))
                    if i == 45:
                        news_in_tick.append(NewsEvent(
                            id=f"news_cap_{i}",
                            timestamp=current_time,
                            headline="MARKET PANIC SEES HIGHEST VOLUME SINCE CYCLE PEAK",
                            content="Panic selling dominates spot orderbooks as margin calls hit leveraged accounts.",
                            sentiment="BEARISH",
                            impact="HIGH"
                        ))
                else:
                    bias = 0.001
                    volume_multiplier = 2.0
                    regime = "SIDEWAYS"
                    risk_mode = "RISK_OFF"

            elif scenario_name.upper() == "BLACK_SWAN":
                if i == 50:
                    bias = -0.25  # Instant catastrophic drop
                    volume_multiplier = 25.0
                    volatility = 0.05
                    regime = "VOLATILE"
                    risk_mode = "RISK_OFF"
                    news_in_tick.append(NewsEvent(
                        id=f"news_bs_{i}",
                        timestamp=current_time,
                        headline="REGULATORY EMERGENCY: SYSTEMIC PROTOCOL EXPLOIT CONFIRMED",
                        content="An unprecedented systemic bug has compromised global liquidity pools. Panic selling underway.",
                        sentiment="BEARISH",
                        impact="HIGH"
                    ))
                    whales_in_tick.append(WhaleEvent(
                        id=f"whale_bs_{i}",
                        timestamp=current_time,
                        event_type="DEX_INFLOW",
                        size=5000.0,
                        value_usd=current_price * 5000,
                        price=current_price,
                        details="Inflow to DEX smart contracts for emergency exits",
                        funding_rate=-0.005,
                        open_interest=open_interest * 0.5
                    ))
                elif 51 <= i <= 60:
                    bias = -0.02
                    volume_multiplier = 5.0
                    volatility = 0.015
                    regime = "BEAR"
                else:
                    bias = 0.0005
                    regime = "SIDEWAYS"

            elif scenario_name.upper() == "WHALE_ACCUMULATION":
                # Oscillation in a tight range with massive whale buy alerts
                bias = 0.0005 * math.sin(i * 0.5)
                volume_multiplier = 1.0 + (1.5 if i % 10 == 0 else 0.0)
                regime = "SIDEWAYS"
                risk_mode = "RISK_ON"
                if i % 10 == 0:
                    whales_in_tick.append(WhaleEvent(
                        id=f"whale_acc_{i}",
                        timestamp=current_time,
                        event_type="LARGE_BUY",
                        size=float(random.randint(300, 900)),
                        value_usd=current_price * 600,
                        price=current_price,
                        details="Iceberg accumulation block filled stealthily",
                        funding_rate=funding_rate,
                        open_interest=open_interest * 1.02
                    ))
                    open_interest *= 1.01

            elif scenario_name.upper() == "WHALE_DISTRIBUTION":
                # Oscillation with large sell alerts and falling open interest
                bias = -0.0004 * math.sin(i * 0.4)
                volume_multiplier = 1.0 + (1.2 if i % 12 == 0 else 0.0)
                regime = "SIDEWAYS"
                risk_mode = "RISK_OFF"
                if i % 12 == 0:
                    whales_in_tick.append(WhaleEvent(
                        id=f"whale_dist_{i}",
                        timestamp=current_time,
                        event_type="LARGE_SELL",
                        size=float(random.randint(400, 1000)),
                        value_usd=current_price * 700,
                        price=current_price,
                        details="Whale OTC/Spot distribution to retail bidding pools",
                        funding_rate=funding_rate,
                        open_interest=open_interest * 0.98
                    ))
                    open_interest *= 0.99

            elif scenario_name.upper() == "ETF_NEWS":
                if i == 30:
                    bias = 0.12  # MASSIVE green candle
                    volume_multiplier = 15.0
                    volatility = 0.02
                    regime = "BULL"
                    risk_mode = "RISK_ON"
                    news_in_tick.append(NewsEvent(
                        id=f"news_etf_{i}",
                        timestamp=current_time,
                        headline="SEC OFFICIALLY APPROVES ALL PENDING CRYPTO ETFs",
                        content="The SEC has approved regulatory changes to list physically-backed crypto ETFs across major US stock exchanges.",
                        sentiment="BULLISH",
                        impact="HIGH"
                    ))
                    whales_in_tick.append(WhaleEvent(
                        id=f"whale_etf_{i}",
                        timestamp=current_time,
                        event_type="LARGE_BUY",
                        size=3000.0,
                        value_usd=current_price * 3000,
                        price=current_price,
                        details="Institutional prime brokerage massive market buy",
                        funding_rate=0.001,
                        open_interest=open_interest * 1.3
                    ))
                    open_interest *= 1.25
                elif 31 <= i <= 45:
                    bias = 0.015
                    volume_multiplier = 3.0
                    volatility = 0.008
                    regime = "BULL"
                else:
                    bias = 0.0002
                    regime = "SIDEWAYS"

            else:
                # Default "RANGE" / standard sideways
                bias = 0.0001 * math.sin(i * 0.3)
                volatility = 0.002
                regime = "SIDEWAYS"

            # Price simulation (geometric brownian-style drift)
            noise = random.normalvariate(0, volatility)
            ret = bias + noise
            close_price = current_price * (1.0 + ret)
            high_price = max(current_price, close_price) * (1.0 + abs(random.normalvariate(0, volatility * 0.5)))
            low_price = min(current_price, close_price) * (1.0 - abs(random.normalvariate(0, volatility * 0.5)))
            volume = float(random.randint(1000, 5000)) * volume_multiplier

            # Compile tick
            candle = Candle(
                symbol=symbol,
                timestamp=current_time,
                open=current_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                timeframe=timeframe
            )

            reg_state = RegimeState(
                timestamp=current_time,
                regime=regime,
                risk_mode=risk_mode,
                description=f"Market simulated as {regime} ({risk_mode})"
            )

            # Generate random simulated scanner alerts during the scenario
            alerts = []
            if random.random() < 0.15:
                alerts.append({
                    "symbol": symbol,
                    "alert_type": "DIVERGENCE" if random.random() < 0.5 else "VOLUME_SPIKE",
                    "message": f"Simulated Scanner Alert: High volume deviation detected for {symbol}",
                    "score": random.randint(60, 95),
                    "timestamp": current_time.isoformat(),
                })

            ticks.append(ReplayTick(
                timestamp=current_time,
                candle=candle,
                news=news_in_tick,
                whales=whales_in_tick,
                regime=reg_state,
                alerts=alerts
            ))

            # Step forward
            current_price = close_price
            current_time += timedelta(minutes=interval_minutes)

        return ticks


class ReplayEngine:
    """Institutional-grade generic Market Replay Engine.

    Statefully handles loading, indexing, slicing, and playing candlestick and
    environmental event timelines. Decoupled from any visual/UI components.
    """

    def __init__(self, ticks: List[ReplayTick]) -> None:
        self.ticks = ticks
        self.current_index = 0
        self.is_playing = False
        self.speed = 1.0  # multiplier: 1x, 2x, 5x, 10x, 100x
        self.playback_mode = "MANUAL"  # MANUAL, AI_ASSISTED, FULL_AI

    @property
    def current_tick(self) -> Optional[ReplayTick]:
        if 0 <= self.current_index < len(self.ticks):
            return self.ticks[self.current_index]
        return None

    @property
    def total_ticks(self) -> int:
        return len(self.ticks)

    @property
    def progress_pct(self) -> float:
        if not self.ticks:
            return 0.0
        return round((self.current_index / len(self.ticks)) * 100, 2)

    def start(self) -> None:
        self.is_playing = True
        logger.info("Replay started at tick %d/%d", self.current_index, len(self.ticks))

    def pause(self) -> None:
        self.is_playing = False
        logger.info("Replay paused at tick %d", self.current_index)

    def resume(self) -> None:
        self.is_playing = True
        logger.info("Replay resumed at tick %d", self.current_index)

    def stop(self) -> None:
        self.is_playing = False
        self.current_index = 0
        logger.info("Replay stopped and reset to start")

    def reset(self) -> None:
        self.current_index = 0
        self.is_playing = False
        logger.info("Replay reset completed")

    def set_speed(self, speed: float) -> None:
        self.speed = speed
        logger.info("Replay speed set to %fx", speed)

    def step(self) -> Optional[ReplayTick]:
        """Advancement of 1 single step (candle)."""
        if self.current_index < len(self.ticks) - 1:
            self.current_index += 1
            return self.ticks[self.current_index]
        else:
            self.is_playing = False
            logger.info("Replay reached end of dataset")
            return None

    def jump_to_date(self, target_date: datetime) -> int:
        """Binary search closest timestamp and jump there."""
        if not self.ticks:
            return 0

        # Ensure target date is timezone-naive/aware aligned
        tz = self.ticks[0].timestamp.tzinfo
        if tz and not target_date.tzinfo:
            target_date = target_date.replace(tzinfo=tz)
        elif not tz and target_date.tzinfo:
            target_date = target_date.replace(tzinfo=None)

        closest_index = 0
        min_diff = abs((self.ticks[0].timestamp - target_date).total_seconds())

        for idx, tick in enumerate(self.ticks):
            diff = abs((tick.timestamp - target_date).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_index = idx

        self.current_index = closest_index
        logger.info("Jumped to index %d for date %s", closest_index, target_date)
        return closest_index

    def get_timeline_history(self) -> List[ReplayTick]:
        """Returns the slice of history from index 0 up to current playing index."""
        return self.ticks[:self.current_index + 1]
