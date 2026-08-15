from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from market_data.pivots import (
    calculate_channel,
    calculate_divergence,
    calculate_levels,
    find_pivots,
)


def test_find_pivots_basic():
    # Construct a baseline df where there are no flat regions
    # using a simple linear gradient so there are no natural sine waves or flat pivots
    highs = [10.0 + 0.1 * i for i in range(21)]
    lows = [5.0 + 0.1 * i for i in range(21)]

    # Force absolute peaks/valleys at specific positions
    highs[10] = 15.0
    lows[15] = 2.0

    df = pd.DataFrame({
        "timestamp": range(100, 121),
        "open": [7.0] * 21,
        "high": highs,
        "low": lows,
        "close": [8.0] * 21,
        "volume": [100.0] * 21,
    })

    pivots = find_pivots(df, window=5)

    # Check pivot high
    high_piv = [p for p in pivots if p[2] == "high"]
    assert len(high_piv) == 1
    assert high_piv[0][1] == 15.0
    assert high_piv[0][3] == 10

    # Check pivot low
    low_piv = [p for p in pivots if p[2] == "low"]
    assert len(low_piv) == 1
    assert low_piv[0][1] == 2.0
    assert low_piv[0][3] == 15


def test_levels_volume_weighted():
    # Construct synthetic data: a price tested ~3 times around 100.0
    # We will run two scenarios: one with low volume on the 100.0 touches,
    # and one with a clear volume spike (high volume) on one of the touches.
    # Base price of 95.0. Pivot highs are set to 100.0. Current price is 95.0, so they should be "resistance".

    def create_df(high_volume_spike):
        # Linear gradient to avoid flat regions or natural wave peaks
        highs = [90.0 + 0.05 * i for i in range(50)]
        lows = [80.0 + 0.05 * i for i in range(50)]
        volumes = [100.0] * 50

        # Three pivot highs around index 10, 25, 40
        highs[10] = 100.0
        highs[25] = 100.1
        highs[40] = 100.2

        if high_volume_spike:
            volumes[25] = 500.0  # Big spike on second touch (5x the average)

        df = pd.DataFrame({
            "timestamp": range(100, 150),
            "open": [92.0] * 50,
            "high": highs,
            "low": lows,
            "close": [93.0] * 50,
            "volume": volumes,
        })
        return df

    df_low_vol = create_df(high_volume_spike=False)
    df_high_vol = create_df(high_volume_spike=True)

    levels_low = calculate_levels(df_low_vol, window=5)
    levels_high = calculate_levels(df_high_vol, window=5)

    # Find the level around 100
    level_low_100 = next(lv for lv in levels_low if abs(lv["price"] - 100.1) <= 1.0)
    level_high_100 = next(lv for lv in levels_high if abs(lv["price"] - 100.1) <= 1.0)

    # Assert type is resistance (since current close is 93.0)
    assert level_low_100["type"] == "resistance"
    assert level_high_100["type"] == "resistance"

    # Assert strength is strictly higher for the high-volume touch
    assert level_high_100["strength"] > level_low_100["strength"]


def test_divergence():
    # Bearish Divergence: price higher high, RSI lower high
    # Bullish Divergence: price lower low, RSI higher low
    # No Divergence: price and RSI moving the same way

    highs = [50.0 + 0.1 * i for i in range(50)]
    lows = [40.0 + 0.1 * i for i in range(50)]
    closes = [45.0 + 0.1 * i for i in range(50)]
    opens = [45.0 + 0.1 * i for i in range(50)]

    # Setup pivots:
    # High at 15
    highs[15] = 60.0
    closes[15] = 59.0
    # High at 35
    highs[35] = 65.0
    closes[35] = 64.0

    # Low at 20
    lows[20] = 30.0
    closes[20] = 31.0
    # Low at 40
    lows[40] = 25.0
    closes[40] = 26.0

    df = pd.DataFrame({
        "timestamp": range(100, 150),
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": [100.0] * 50,
    })

    # Case 1: Bearish Divergence. Price highs are higher (60 -> 65), RSI is lower (70 -> 60)
    mock_rsi_bearish = pd.Series([50.0] * 50)
    mock_rsi_bearish.iloc[15] = 70.0
    mock_rsi_bearish.iloc[35] = 60.0

    with patch("pandas_ta.rsi", return_value=mock_rsi_bearish):
        res = calculate_divergence(df, window=5)
        assert res["found"] is True
        assert res["type"] == "bearish"
        assert res["p1"]["price"] == 60.0
        assert res["p2"]["price"] == 65.0
        assert res["p1"]["rsi"] == 70.0
        assert res["p2"]["rsi"] == 60.0

    # Case 2: Bullish Divergence. Price lows are lower (30 -> 25), RSI is higher (30 -> 40)
    mock_rsi_bullish = pd.Series([50.0] * 50)
    mock_rsi_bullish.iloc[20] = 30.0
    mock_rsi_bullish.iloc[40] = 40.0

    with patch("pandas_ta.rsi", return_value=mock_rsi_bullish):
        res = calculate_divergence(df, window=5)
        assert res["found"] is True
        assert res["type"] == "bullish"
        assert res["p1"]["price"] == 30.0
        assert res["p2"]["price"] == 25.0
        assert res["p1"]["rsi"] == 30.0
        assert res["p2"]["rsi"] == 40.0

    # Case 3: No Divergence. Price highs higher (60 -> 65), RSI higher (60 -> 70)
    mock_rsi_none = pd.Series([50.0] * 50)
    mock_rsi_none.iloc[15] = 60.0
    mock_rsi_none.iloc[35] = 70.0
    mock_rsi_none.iloc[20] = 40.0
    mock_rsi_none.iloc[40] = 30.0

    with patch("pandas_ta.rsi", return_value=mock_rsi_none):
        res = calculate_divergence(df, window=5)
        assert res["found"] is False
        assert res["type"] == "none"


def test_channel():
    # Scenario 1: Ascending channel
    # High pivots at 10, 20, 30. Low pivots at 15, 25, 35.
    # Linear trend wave baseline
    highs = [100.0 + 0.5 * i for i in range(50)]
    lows = [90.0 + 0.5 * i for i in range(50)]
    closes = [95.0 + 0.5 * i for i in range(50)]
    opens = [95.0 + 0.5 * i for i in range(50)]

    # Set pivot highs at 10, 20, 30
    highs[10] += 5.0
    highs[20] += 5.0
    highs[30] += 5.0
    # Set pivot lows at 15, 25, 35
    lows[15] -= 5.0
    lows[25] -= 5.0
    lows[35] -= 5.0

    df_asc = pd.DataFrame({
        "timestamp": range(100, 150),
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })

    res = calculate_channel(df_asc, window=4)
    assert res["found"] is True
    assert res["direction"] == "up"
    assert "upper" in res
    assert "lower" in res

    # Scenario 2: Non-parallel channel
    df_non_parallel = df_asc.copy()
    # Change lows to NOT be parallel: slope is completely different
    df_non_parallel.loc[15, "low"] -= 20.0
    df_non_parallel.loc[25, "low"] += 5.0
    df_non_parallel.loc[35, "low"] += 40.0

    res_none = calculate_channel(df_non_parallel, window=4)
    assert res_none["found"] is False


# ─── Integration tests for the new API endpoints ─────────────────────────

def test_api_market_levels(api_client):
    # Mock get_ohlcv to return dummy data with pivots
    dummy_df = pd.DataFrame({
        "timestamp": range(100, 150),
        "open": [100.0] * 50,
        "high": [100.0] * 50,
        "low": [100.0] * 50,
        "close": [100.0] * 50,
        "volume": [10.0] * 50,
    })
    dummy_df.loc[10, "high"] = 110.0
    dummy_df.loc[25, "high"] = 110.0
    dummy_df.loc[40, "high"] = 110.0

    with patch("market.provider.multi.MultiProvider.get_ohlcv", return_value=dummy_df):
        resp = api_client.get("/market/levels?symbol=BTC&timeframe=1h")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) > 0
        assert "price" in body[0]
        assert "type" in body[0]
        assert "strength" in body[0]


def test_api_market_divergence(api_client):
    dummy_df = pd.DataFrame({
        "timestamp": range(100, 150),
        "open": [100.0] * 50,
        "high": [100.0] * 50,
        "low": [100.0] * 50,
        "close": [100.0] * 50,
        "volume": [10.0] * 50,
    })
    with patch("market.provider.multi.MultiProvider.get_ohlcv", return_value=dummy_df):
        resp = api_client.get("/market/divergence?symbol=BTC&timeframe=1h")
        assert resp.status_code == 200
        body = resp.json()
        assert "found" in body
        assert "type" in body


def test_api_market_channel(api_client):
    dummy_df = pd.DataFrame({
        "timestamp": range(100, 150),
        "open": [100.0] * 50,
        "high": [100.0] * 50,
        "low": [100.0] * 50,
        "close": [100.0] * 50,
        "volume": [10.0] * 50,
    })
    with patch("market.provider.multi.MultiProvider.get_ohlcv", return_value=dummy_df):
        resp = api_client.get("/market/channel?symbol=BTC&timeframe=1h")
        assert resp.status_code == 200
        body = resp.json()
        assert "found" in body
        assert "direction" in body
