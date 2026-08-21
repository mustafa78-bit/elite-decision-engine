from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from market_data.pivots import (
    calculate_channel,
    calculate_divergence,
    calculate_levels,
    calculate_liquidity_zones,
    calculate_volume_profile,
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


def test_channel_does_not_extrapolate_back_before_the_earliest_pivot():
    # 150 flat candles, then a clean ascending channel only in the LAST 40 --
    # confirmed live 2026-08-20: extrapolating the fitted line back to
    # index 0 regardless of where the pivots actually sit turned this into
    # a line shooting off like a ray, dwarfing the real candles once the
    # chart auto-fit to include it.
    n_flat = 150
    highs = [100.0] * n_flat
    lows = [90.0] * n_flat
    closes = [95.0] * n_flat
    opens = [95.0] * n_flat

    n_channel = 50
    highs += [200.0 + 0.5 * i for i in range(n_channel)]
    lows += [190.0 + 0.5 * i for i in range(n_channel)]
    closes += [195.0 + 0.5 * i for i in range(n_channel)]
    opens += [195.0 + 0.5 * i for i in range(n_channel)]

    highs[n_flat + 10] += 5.0
    highs[n_flat + 20] += 5.0
    highs[n_flat + 30] += 5.0
    lows[n_flat + 15] -= 5.0
    lows[n_flat + 25] -= 5.0
    lows[n_flat + 35] -= 5.0

    total = n_flat + n_channel
    df = pd.DataFrame({
        "timestamp": range(1000, 1000 + total),
        "open": opens, "high": highs, "low": lows, "close": closes,
    })

    res = calculate_channel(df, window=4)
    assert res["found"] is True
    # The line must start at or after the earliest pivot (index n_flat + 10
    # at the very earliest), never at candle 0 of the flat lead-in.
    assert res["upper"]["start"]["time"] >= 1000 + n_flat
    assert res["lower"]["start"]["time"] >= 1000 + n_flat
    # And its price must stay within a sane range of the real channel data,
    # not shoot off far below/above it from backward extrapolation.
    assert 150.0 <= res["upper"]["start"]["price"] <= 260.0
    assert 150.0 <= res["lower"]["start"]["price"] <= 260.0


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


class TestCalculateLiquidityZones:

    def test_unswept_pivots_are_reported(self):
        # Same shape as test_find_pivots_basic: a forced pivot high that's
        # never exceeded afterward, and a forced pivot low never undercut
        # afterward -- both should surface as unswept liquidity zones.
        highs = [10.0 + 0.1 * i for i in range(21)]
        lows = [5.0 + 0.1 * i for i in range(21)]
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

        zones = calculate_liquidity_zones(df, window=5)

        sell_side = [z for z in zones if z["type"] == "sell_side"]
        buy_side = [z for z in zones if z["type"] == "buy_side"]
        assert len(sell_side) == 1
        assert sell_side[0]["price"] == 15.0
        assert len(buy_side) == 1
        assert buy_side[0]["price"] == 2.0

    def test_swept_zone_is_excluded(self):
        # Same pivot-high setup, but a later candle trades above it --
        # that liquidity has already been taken, must not be reported.
        highs = [10.0 + 0.1 * i for i in range(25)]
        lows = [5.0] * 25
        highs[10] = 15.0
        highs[20] = 16.0  # sweeps the pivot at index 10

        df = pd.DataFrame({
            "timestamp": range(100, 125),
            "open": [7.0] * 25,
            "high": highs,
            "low": lows,
            "close": [8.0] * 25,
            "volume": [100.0] * 25,
        })

        zones = calculate_liquidity_zones(df, window=5)
        sell_side_at_15 = [z for z in zones if z["type"] == "sell_side" and z["price"] == 15.0]
        assert sell_side_at_15 == []

    def test_equal_highs_cluster_into_one_stronger_zone(self):
        # Two pivot highs at almost the same price ("equal highs") must
        # merge into a single zone with touches=2, not two separate zones.
        highs = [10.0] * 31
        lows = [5.0] * 31
        highs[5] = 20.0
        highs[6] = 12.0  # dip so index 5 and index 15 are both real pivots
        highs[15] = 20.05  # within 0.3% of 20.0
        highs[16] = 12.0

        df = pd.DataFrame({
            "timestamp": range(100, 131),
            "open": [7.0] * 31,
            "high": highs,
            "low": lows,
            "close": [8.0] * 31,
            "volume": [100.0] * 31,
        })

        zones = calculate_liquidity_zones(df, window=5, pct_tol=0.003)
        sell_side = [z for z in zones if z["type"] == "sell_side"]
        assert len(sell_side) == 1
        assert sell_side[0]["touches"] == 2

    def test_empty_df_returns_empty_list(self):
        assert calculate_liquidity_zones(pd.DataFrame()) == []

    def test_capped_at_5_strongest_zones(self):
        # Real reported bug 2026-08-21: an uncapped zone list rendered as
        # 8-10 overlapping, unreadable price-axis labels once several
        # zones landed close together. Build a df with well more than 5
        # distinct, unswept, non-clustering pivot highs.
        n = 200
        highs = [10.0] * n
        lows = [5.0] * n
        # Spaced far enough apart in price (2.0 each) to never cluster
        # (pct_tol=0.003 is well under that), and each isolated by dips on
        # both sides so every one is a real, individually-unswept pivot.
        peak_prices = [12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0]
        peak_indices = [10, 30, 50, 70, 90, 110, 130, 150]
        for price, idx in zip(peak_prices, peak_indices):
            highs[idx] = price

        df = pd.DataFrame({
            "timestamp": range(1000, 1000 + n),
            "open": [7.0] * n,
            "high": highs,
            "low": lows,
            "close": [8.0] * n,
            "volume": [100.0] * n,
        })

        zones = calculate_liquidity_zones(df, window=5)
        assert len(zones) <= 5


class TestCalculateVolumeProfile:

    def test_poc_is_the_highest_volume_bin(self):
        # Flat, narrow-range candles except one huge-volume candle near the
        # top of the range -- POC must land in that price area.
        n = 30
        df = pd.DataFrame({
            "timestamp": range(100, 100 + n),
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.0] * n,
            "volume": [10.0] * n,
        })
        df.loc[15, ["low", "high"]] = [109.5, 110.0]
        df.loc[15, "volume"] = 10000.0

        profile = calculate_volume_profile(df, num_bins=20)
        assert profile["poc_price"] is not None
        assert 109.0 <= profile["poc_price"] <= 110.5

    def test_bins_conserve_total_volume(self):
        n = 20
        df = pd.DataFrame({
            "timestamp": range(100, 100 + n),
            "open": [100.0] * n,
            "high": [105.0] * n,
            "low": [95.0] * n,
            "close": [100.0] * n,
            "volume": [50.0] * n,
        })
        profile = calculate_volume_profile(df, num_bins=10)
        total_binned = sum(b["volume"] for b in profile["bins"])
        assert total_binned == pytest.approx(sum(df["volume"]), rel=1e-6)

    def test_value_area_contains_poc(self):
        n = 20
        df = pd.DataFrame({
            "timestamp": range(100, 100 + n),
            "open": [100.0] * n,
            "high": [105.0] * n,
            "low": [95.0] * n,
            "close": [100.0] * n,
            "volume": [50.0] * n,
        })
        profile = calculate_volume_profile(df, num_bins=10)
        assert profile["value_area_low"] <= profile["poc_price"] <= profile["value_area_high"]

    def test_empty_df_returns_empty_profile(self):
        profile = calculate_volume_profile(pd.DataFrame())
        assert profile["bins"] == []
        assert profile["poc_price"] is None


def test_api_market_liquidity_zones(api_client):
    highs = [10.0 + 0.1 * i for i in range(21)]
    lows = [5.0 + 0.1 * i for i in range(21)]
    highs[10] = 15.0
    lows[15] = 2.0
    dummy_df = pd.DataFrame({
        "timestamp": range(100, 121),
        "open": [7.0] * 21,
        "high": highs,
        "low": lows,
        "close": [8.0] * 21,
        "volume": [100.0] * 21,
    })
    with patch("market.provider.multi.MultiProvider.get_ohlcv", return_value=dummy_df):
        resp = api_client.get("/market/liquidity-zones?symbol=BTC&timeframe=1h")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert any(z["type"] == "sell_side" for z in body)
        assert any(z["type"] == "buy_side" for z in body)


def test_api_market_volume_profile(api_client):
    dummy_df = pd.DataFrame({
        "timestamp": range(100, 150),
        "open": [100.0] * 50,
        "high": [105.0] * 50,
        "low": [95.0] * 50,
        "close": [100.0] * 50,
        "volume": [10.0] * 50,
    })
    with patch("market.provider.multi.MultiProvider.get_ohlcv", return_value=dummy_df):
        resp = api_client.get("/market/volume-profile?symbol=BTC&timeframe=1h&num_bins=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "bins" in body
        assert "poc_price" in body
        assert len(body["bins"]) == 10
