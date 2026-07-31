from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd

from simulator.models import ScenarioType

ScenarioDefinition = dict[str, Any]

SCENARIOS: dict[ScenarioType, ScenarioDefinition] = {
    ScenarioType.FLASH_CRASH: {
        "name": "Flash Crash",
        "description": "Sudden market crash followed by rapid recovery. Tests panic discipline and stop-loss placement.",
        "drift": -0.05,
        "volatility": 0.08,
        "recovery_drift": 0.03,
        "duration_candles": 50,
    },
    ScenarioType.BULL_RUN: {
        "name": "Bull Run",
        "description": "Sustained upward momentum with high volume. Tests trend following and profit-taking discipline.",
        "drift": 0.01,
        "volatility": 0.03,
        "duration_candles": 200,
    },
    ScenarioType.CAPITULATION: {
        "name": "Capitulation",
        "description": "Extended sell-off with panic selling climax. Tests risk management and bottom-fishing.",
        "drift": -0.015,
        "volatility": 0.05,
        "capitulation_volatility": 0.12,
        "duration_candles": 100,
    },
    ScenarioType.RANGE: {
        "name": "Range Bound",
        "description": "Price oscillates within a tight range. Tests patience and range-trading strategy.",
        "drift": 0.0,
        "volatility": 0.01,
        "range_width": 0.03,
        "duration_candles": 150,
    },
    ScenarioType.WHALE_ACCUMULATION: {
        "name": "Whale Accumulation",
        "description": "Large player accumulating position with suppression. Tests detection of institutional activity.",
        "drift": -0.002,
        "volatility": 0.015,
        "whale_buy_pressure": 0.8,
        "duration_candles": 120,
    },
    ScenarioType.WHALE_DISTRIBUTION: {
        "name": "Whale Distribution",
        "description": "Large player distributing position with pumps. Tests distribution pattern recognition.",
        "drift": 0.005,
        "volatility": 0.025,
        "whale_sell_pressure": 0.7,
        "duration_candles": 120,
    },
    ScenarioType.ETF_NEWS: {
        "name": "ETF Approval News",
        "description": "Sudden regulatory news causing explosive move. Tests news-aware decision making.",
        "drift": 0.001,
        "volatility": 0.02,
        "news_shock": 0.15,
        "news_candle": 80,
        "duration_candles": 150,
    },
    ScenarioType.EXCHANGE_LISTING: {
        "name": "Exchange Listing",
        "description": "New exchange listing drives volume and price discovery. Tests liquidity-aware trading.",
        "drift": 0.003,
        "volatility": 0.04,
        "volume_spike": 5.0,
        "duration_candles": 100,
    },
    ScenarioType.BLACK_SWAN: {
        "name": "Black Swan Event",
        "description": "Unpredictable catastrophic event. Tests worst-case scenario preparation.",
        "drift": -0.001,
        "volatility": 0.02,
        "crash_magnitude": -0.30,
        "crash_candle": 60,
        "duration_candles": 200,
    },
}


def generate_scenario_data(
    scenario_type: ScenarioType,
    symbol: str = "BTC",
    timeframe: str = "1h",
    num_candles: int = 200,
    start_price: Optional[float] = None,
) -> pd.DataFrame:
    cfg = SCENARIOS.get(scenario_type)
    if cfg is None:
        cfg = SCENARIOS[ScenarioType.RANGE]

    base = start_price or {
        "BTC": 30000.0, "ETH": 2000.0, "SOL": 100.0, "HYPE": 500.0,
    }.get(symbol, 100.0)

    seed = hash(f"{symbol}{scenario_type.value}") % 10000
    rng = random.Random(seed)
    ms = {"1m": 60000, "5m": 300000, "15m": 900000, "1h": 3600000, "4h": 14400000, "1d": 86400000}.get(timeframe, 3600000)
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    times = [now - (num_candles - i) * ms for i in range(num_candles)]

    drift = cfg.get("drift", 0.0)
    volatility = cfg.get("volatility", 0.02)
    price = base
    data: list[dict[str, Any]] = []

    for i in range(num_candles):
        d = drift
        v = volatility

        if scenario_type == ScenarioType.FLASH_CRASH:
            crash_start = num_candles // 3
            crash_end = crash_start + 15
            if crash_start <= i < crash_end:
                d = cfg["recovery_drift"] if i > crash_start + 5 else -0.08
                v = cfg["volatility"]
            elif i >= crash_end:
                d = cfg["recovery_drift"]
                v = cfg["volatility"] * 0.6

        elif scenario_type == ScenarioType.CAPITULATION:
            if i > num_candles * 0.6:
                v = cfg["capitulation_volatility"]
                d = -0.03
            if i > num_candles * 0.85:
                d = 0.02

        elif scenario_type == ScenarioType.RANGE:
            if price > base * (1 + cfg["range_width"]):
                d = -0.005
            elif price < base * (1 - cfg["range_width"]):
                d = 0.005

        elif scenario_type == ScenarioType.WHALE_ACCUMULATION:
            if i % 10 < 3:
                d = -0.008
            elif i % 10 == 3:
                d = 0.02

        elif scenario_type == ScenarioType.WHALE_DISTRIBUTION:
            if i % 10 < 3:
                d = 0.015
            elif i % 10 == 3:
                d = -0.025

        elif scenario_type == ScenarioType.ETF_NEWS:
            news_candle = cfg.get("news_candle", 80)
            if i == news_candle:
                d = cfg.get("news_shock", 0.1)
                v = cfg.get("volatility", 0.02) * 3

        elif scenario_type == ScenarioType.BLACK_SWAN:
            crash_candle = cfg.get("crash_candle", 60)
            if i == crash_candle:
                d = cfg.get("crash_magnitude", -0.25)
                v = 0.15
            elif i > crash_candle and i < crash_candle + 20:
                v = 0.08

        elif scenario_type == ScenarioType.EXCHANGE_LISTING:
            if 40 <= i < 50:
                v = cfg.get("volatility", 0.04) * 2
                d = 0.02
            vol_mult = cfg.get("volume_spike", 1.0)

        ret = rng.gauss(d, v)
        price *= 1 + ret
        o = round(price / (1 + ret), 2)
        h = round(price * (1 + abs(rng.gauss(0, v * 0.5))), 2)
        l = round(price * (1 - abs(rng.gauss(0, v * 0.5))), 2)
        vol = rng.uniform(100, 10000)
        data.append({
            "timestamp": times[i],
            "open": o,
            "high": h,
            "low": l,
            "close": round(price, 2),
            "volume": round(vol, 2),
        })

    return pd.DataFrame(data)
