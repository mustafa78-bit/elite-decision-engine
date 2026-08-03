import numpy as np
import pandas as pd
import pandas_ta as ta


def find_pivots(df: pd.DataFrame, window: int = 5):
    """
    Finds local pivot highs/lows in an OHLC DataFrame.
    A candle at index i is a pivot high if its high is the max within window candles on each side.
    A candle at index i is a pivot low if its low is the min within window candles on each side.
    We also require that a pivot high is strictly greater than its immediate left and right neighbors,
    and a pivot low is strictly less than its immediate left and right neighbors, to prevent flat regions
    from being detected as pivots.

    Returns:
        List of tuples: (timestamp_or_index, price, "high" | "low", index)
    """
    pivots = []
    if len(df) < 2 * window + 1:
        return pivots

    highs = df["high"].values
    lows = df["low"].values
    has_timestamp = "timestamp" in df.columns

    for i in range(window, len(df) - window):
        current_high = highs[i]
        current_low = lows[i]

        window_highs = highs[i - window : i + window + 1]
        window_lows = lows[i - window : i + window + 1]

        is_high = (
            current_high == np.max(window_highs) and
            current_high > highs[i - 1] and
            current_high > highs[i + 1]
        )
        is_low = (
            current_low == np.min(window_lows) and
            current_low < lows[i - 1] and
            current_low < lows[i + 1]
        )

        idx_val = int(df["timestamp"].iloc[i]) if has_timestamp else i

        if is_high:
            pivots.append((idx_val, float(current_high), "high", i))
        if is_low:
            pivots.append((idx_val, float(current_low), "low", i))

    return pivots


def get_volume_ratio_score(df: pd.DataFrame, i: int):
    """
    Computes a VolumeEngine-style ratio and score for a given index i.
    Uses the volume at index i versus the 20-period average of volume ending at index i.
    """
    volume_now = float(df["volume"].iloc[i])
    # Average of up to 20 periods up to i
    prev_slice = df["volume"].iloc[max(0, i - 19) : i + 1]
    volume_avg = float(prev_slice.mean()) if not prev_slice.empty else 1.0
    if volume_avg == 0:
        volume_avg = 1.0

    ratio = volume_now / volume_avg

    if ratio >= 2.0:
        score = 1.0
    elif ratio >= 1.5:
        score = 0.8
    elif ratio >= 1.2:
        score = 0.7
    elif ratio >= 1.0:
        score = 0.5
    else:
        score = 0.3

    return ratio, score


def calculate_levels(df: pd.DataFrame, window: int = 5, pct_tol: float = 0.005):
    """
    Using find_pivots, cluster nearby pivot price levels together (within ~0.5% of price).
    For each clustered level, compute a strength score from:
      (a) touch count
      (b) VolumeEngine-style volume ratio/score at each touch.
    Classify each level as "support" or "resistance" relative to current price.
    Cap output at top 5 by strength.

    Returns:
        List of dicts: [{"price": float, "type": "support"|"resistance", "strength": float, "touches": int}]
    """
    if df.empty:
        return []

    current_price = float(df["close"].iloc[-1])
    pivots = find_pivots(df, window=window)
    if not pivots:
        return []

    # Sort pivots by price for easier grouping/clustering
    sorted_pivots = sorted(pivots, key=lambda x: x[1])

    clusters = []
    current_cluster = [sorted_pivots[0]]

    for p in sorted_pivots[1:]:
        # Compare price with the average of current cluster
        avg_price = sum(x[1] for x in current_cluster) / len(current_cluster)
        if abs(p[1] - avg_price) / avg_price <= pct_tol:
            current_cluster.append(p)
        else:
            clusters.append(current_cluster)
            current_cluster = [p]
    if current_cluster:
        clusters.append(current_cluster)

    levels = []
    for cl in clusters:
        # price level is the average of prices in this cluster
        level_price = sum(x[1] for x in cl) / len(cl)

        total_strength = 0.0
        for p in cl:
            # p is (timestamp, price, type, index)
            idx = p[3]
            _, vol_score = get_volume_ratio_score(df, idx)
            # High-volume touches increase strength vs low-volume touches
            total_strength += (1.0 + vol_score)

        level_type = "support" if level_price < current_price else "resistance"
        levels.append({
            "price": round(level_price, 4),
            "type": level_type,
            "strength": round(total_strength, 4),
            "touches": len(cl)
        })

    # Sort by strength descending, and limit to top 5
    levels = sorted(levels, key=lambda x: x["strength"], reverse=True)[:5]
    return levels


def calculate_divergence(df: pd.DataFrame, window: int = 5):
    """
    RSI(14) divergence detection.
    Computes full RSI series using df.ta.rsi(length=14).
    Uses find_pivots to get the pivot points, then compares RSI's value at those same indexes/timestamps.

    - Bearish: price's most recent pivot high is HIGHER than its previous pivot high,
      but RSI's value at the recent pivot is LOWER than RSI's value at the previous pivot.
    - Bullish: price's most recent pivot low is LOWER than its previous pivot low,
      but RSI's value at the recent pivot is HIGHER than at the previous pivot.

    Returns:
        dict: {
            "found": bool,
            "type": "bullish" | "bearish" | "none",
            "p1": {"time": int, "price": float, "rsi": float},
            "p2": {"time": int, "price": float, "rsi": float}
        } (or empty/none if nothing detected)
    """
    res = {"found": False, "type": "none", "p1": None, "p2": None}
    if df.empty or len(df) < 15:
        return res

    df = df.copy()
    rsi_series = ta.rsi(df["close"], length=14)
    if rsi_series is None or rsi_series.isna().all():
        return res

    pivots = find_pivots(df, window=window)
    if not pivots:
        return res

    high_pivots = [p for p in pivots if p[2] == "high"]
    low_pivots = [p for p in pivots if p[2] == "low"]

    # Check Bearish Divergence (on pivot highs)
    # We need at least 2 pivot highs. We examine the last 2.
    if len(high_pivots) >= 2:
        prev_h = high_pivots[-2]
        rec_h = high_pivots[-1]

        prev_price = prev_h[1]
        rec_price = rec_h[1]

        prev_idx = prev_h[3]
        rec_idx = rec_h[3]

        prev_rsi = rsi_series.iloc[prev_idx]
        rec_rsi = rsi_series.iloc[rec_idx]

        if not pd.isna(prev_rsi) and not pd.isna(rec_rsi):
            if rec_price > prev_price and rec_rsi < prev_rsi:
                return {
                    "found": True,
                    "type": "bearish",
                    "p1": {"time": int(prev_h[0]), "price": float(prev_price), "rsi": float(prev_rsi)},
                    "p2": {"time": int(rec_h[0]), "price": float(rec_price), "rsi": float(rec_rsi)}
                }

    # Check Bullish Divergence (on pivot lows)
    if len(low_pivots) >= 2:
        prev_l = low_pivots[-2]
        rec_l = low_pivots[-1]

        prev_price = prev_l[1]
        rec_price = rec_l[1]

        prev_idx = prev_l[3]
        rec_idx = rec_l[3]

        prev_rsi = rsi_series.iloc[prev_idx]
        rec_rsi = rsi_series.iloc[rec_idx]

        if not pd.isna(prev_rsi) and not pd.isna(rec_rsi):
            if rec_price < prev_price and rec_rsi > prev_rsi:
                return {
                    "found": True,
                    "type": "bullish",
                    "p1": {"time": int(prev_l[0]), "price": float(prev_price), "rsi": float(prev_rsi)},
                    "p2": {"time": int(rec_l[0]), "price": float(rec_price), "rsi": float(rec_rsi)}
                }

    return res


def calculate_channel(df: pd.DataFrame, window: int = 5, pct_tol: float = 0.003):
    """
    Fits simple linear regression lines through recent swing lows (lower boundary)
    and swing highs (upper boundary) found with find_pivots.

    Only reports a channel if:
      - The two lines are roughly parallel (slopes are within slope tolerance,
        sensible definition: the difference in slope as a percentage of current price
        is <= pct_tol, i.e., |slope_high - slope_low| / current_price <= pct_tol)
      - Each side has at least 3 points.

    Returns:
        dict: {
            "found": bool,
            "direction": "up" | "down" | "sideways" | "none",
            "upper": {"start": {"time": int, "price": float}, "end": {"time": int, "price": float}},
            "lower": {"start": {"time": int, "price": float}, "end": {"time": int, "price": float}}
        }
    """
    res = {"found": False, "direction": "none", "upper": None, "lower": None}
    if df.empty:
        return res

    current_price = float(df["close"].iloc[-1])
    pivots = find_pivots(df, window=window)
    if not pivots:
        return res

    high_pivots = [p for p in pivots if p[2] == "high"]
    low_pivots = [p for p in pivots if p[2] == "low"]

    if len(high_pivots) < 3 or len(low_pivots) < 3:
        return res

    # Fit line through highs: y = m*x + c
    # x is the candle index, y is the price
    x_high = np.array([p[3] for p in high_pivots], dtype=float)
    y_high = np.array([p[1] for p in high_pivots], dtype=float)

    m_high, c_high = np.polyfit(x_high, y_high, 1)

    # Fit line through lows
    x_low = np.array([p[3] for p in low_pivots], dtype=float)
    y_low = np.array([p[1] for p in low_pivots], dtype=float)

    m_low, c_low = np.polyfit(x_low, y_low, 1)

    # Check if slopes are roughly parallel
    # Let's check slope difference normalized by current price.
    # A tolerance of pct_tol (e.g. 0.003 = 0.3% of price per candle)
    slope_diff = abs(m_high - m_low)

    if (slope_diff / current_price) > pct_tol:
        return res

    # Valid channel found!
    # Determine trend direction from slope.
    # Average slope: m_avg = (m_high + m_low) / 2
    # If positive trend: "up", negative trend: "down", otherwise: "sideways"
    # Sideways if absolute slope per candle is less than e.g. 0.01% of price.
    m_avg = (m_high + m_low) / 2.0
    slope_pct = m_avg / current_price

    if slope_pct > 0.0001:  # +0.01% per candle
        direction = "up"
    elif slope_pct < -0.0001:  # -0.01% per candle
        direction = "down"
    else:
        direction = "sideways"

    # We want start/end pairs. Start is first candle index (0), end is last candle index (len(df) - 1).
    # This draws the lines across the entire visible chart cleanly!
    has_timestamp = "timestamp" in df.columns

    idx_start = 0
    idx_end = len(df) - 1

    time_start = int(df["timestamp"].iloc[idx_start]) if has_timestamp else idx_start
    time_end = int(df["timestamp"].iloc[idx_end]) if has_timestamp else idx_end

    y_high_start = m_high * idx_start + c_high
    y_high_end = m_high * idx_end + c_high

    y_low_start = m_low * idx_start + c_low
    y_low_end = m_low * idx_end + c_low

    return {
        "found": True,
        "direction": direction,
        "upper": {
            "start": {"time": time_start, "price": round(y_high_start, 4)},
            "end": {"time": time_end, "price": round(y_high_end, 4)}
        },
        "lower": {
            "start": {"time": time_start, "price": round(y_low_start, 4)},
            "end": {"time": time_end, "price": round(y_low_end, 4)}
        }
    }
