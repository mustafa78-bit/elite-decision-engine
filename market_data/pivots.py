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

    # Draw the lines only across the span the regression is actually
    # supported by: from the earliest pivot used in the fit through to the
    # current candle. Extrapolating all the way back to index 0 (the start
    # of the whole fetched window, e.g. 200 candles) regardless of where
    # the pivots actually are produced wildly exaggerated lines shooting
    # off like a ray whenever the pivots were clustered in a small, recent
    # index range but the fitted slope was non-trivial -- confirmed live
    # 2026-08-20. Extending forward to the last candle is kept: that's the
    # useful "where does the channel put price right now" projection.
    has_timestamp = "timestamp" in df.columns

    idx_start = int(min(x_high.min(), x_low.min()))
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


def calculate_liquidity_zones(df: pd.DataFrame, window: int = 5, pct_tol: float = 0.003):
    """
    Swing-based liquidity pools (ICT/SMC concept): resting stop/liquidation
    orders are assumed to cluster just beyond swing points -- sell-side
    liquidity (SSL) just above swing highs, buy-side liquidity (BSL) just
    below swing lows. Reuses find_pivots() (the same swing-point detector
    calculate_levels()/calculate_channel() already use) rather than a
    second, separate pivot algorithm.

    Two refinements beyond a single pivot:
      - Equal-highs/equal-lows clustering: pivots of the SAME type within
        pct_tol of each other's average price are merged into one zone with
        a higher `strength` (touch count) -- multiple swings failing at
        almost the same price is a stronger real-world liquidity signal
        than any single pivot, and is a named concept ("equal highs/lows")
        in its own right.
      - Swept-zone filtering: a zone is only reported if no LATER candle in
        the series has already traded through it (a swing high's zone is
        swept once a later candle's high exceeds it; a swing low's zone is
        swept once a later candle's low goes below it). An already-swept
        pool is stale, not a real target -- reporting it would be
        misleading, not just uninteresting.

    Returns:
        List of dicts, sorted by strength descending, capped at 5 (same as
        calculate_levels() above -- more than that overlaps into unreadable
        labels on a chart's price axis):
        [{"price": float, "type": "buy_side"|"sell_side", "strength": int,
          "touches": int}]
    """
    if df.empty:
        return []

    pivots = find_pivots(df, window=window)
    if not pivots:
        return []

    highs = df["high"].values
    lows = df["low"].values

    def _cluster(same_type_pivots: list) -> list:
        if not same_type_pivots:
            return []
        sorted_p = sorted(same_type_pivots, key=lambda x: x[1])
        clusters = [[sorted_p[0]]]
        for p in sorted_p[1:]:
            avg_price = sum(x[1] for x in clusters[-1]) / len(clusters[-1])
            if avg_price > 0 and abs(p[1] - avg_price) / avg_price <= pct_tol:
                clusters[-1].append(p)
            else:
                clusters.append([p])
        return clusters

    zones = []

    high_pivots = [p for p in pivots if p[2] == "high"]
    for cluster in _cluster(high_pivots):
        level_price = sum(x[1] for x in cluster) / len(cluster)
        # Swept if any candle strictly after the LAST pivot in this cluster
        # already traded above it.
        last_idx = max(x[3] for x in cluster)
        if last_idx + 1 < len(highs) and highs[last_idx + 1:].max() > level_price:
            continue
        zones.append({
            "price": round(level_price, 4),
            "type": "sell_side",
            "strength": len(cluster),
            "touches": len(cluster),
        })

    low_pivots = [p for p in pivots if p[2] == "low"]
    for cluster in _cluster(low_pivots):
        level_price = sum(x[1] for x in cluster) / len(cluster)
        last_idx = max(x[3] for x in cluster)
        if last_idx + 1 < len(lows) and lows[last_idx + 1:].min() < level_price:
            continue
        zones.append({
            "price": round(level_price, 4),
            "type": "buy_side",
            "strength": len(cluster),
            "touches": len(cluster),
        })

    # Capped at 5, same as calculate_levels() above -- an uncapped list
    # rendered as price-line labels on the chart's right axis produced 8-10
    # overlapping, unreadable labels once several zones landed close
    # together in price. Confirmed live 2026-08-21.
    return sorted(zones, key=lambda z: z["strength"], reverse=True)[:5]


def calculate_volume_profile(df: pd.DataFrame, num_bins: int = 24):
    """
    Volume-at-price histogram over the visible candle range. Without raw
    tick data, each candle's volume is distributed evenly across every
    price bin its [low, high] range overlaps -- the standard approximation
    used when only OHLCV candles (not individual trades) are available.

    Also reports the Point of Control (POC, the single highest-volume bin)
    and the Value Area (the smallest set of bins containing >= 70% of
    total volume, built outward from the POC) -- both standard volume
    profile concepts, not custom to this implementation.

    Returns:
        dict: {
            "bins": [{"price_low": float, "price_high": float, "volume": float}, ...],
            "poc_price": float | None,
            "value_area_high": float | None,
            "value_area_low": float | None,
        }
    """
    empty = {"bins": [], "poc_price": None, "value_area_high": None, "value_area_low": None}
    if df.empty or num_bins < 1:
        return empty

    price_min = float(df["low"].min())
    price_max = float(df["high"].max())
    if price_max <= price_min:
        return empty

    bin_size = (price_max - price_min) / num_bins
    bin_volumes = [0.0] * num_bins

    for _, row in df.iterrows():
        low, high, volume = float(row["low"]), float(row["high"]), float(row["volume"])
        if volume <= 0:
            continue
        candle_range = high - low
        first_bin = min(int((low - price_min) / bin_size), num_bins - 1)
        last_bin = min(int((high - price_min) / bin_size), num_bins - 1)
        if first_bin == last_bin or candle_range <= 0:
            bin_volumes[first_bin] += volume
            continue
        # Distribute proportional to how much of the candle's range falls in
        # each bin it overlaps.
        for b in range(first_bin, last_bin + 1):
            bin_low = price_min + b * bin_size
            bin_high = bin_low + bin_size
            overlap = min(high, bin_high) - max(low, bin_low)
            if overlap > 0:
                bin_volumes[b] += volume * (overlap / candle_range)

    bins = [
        {
            "price_low": round(price_min + i * bin_size, 4),
            "price_high": round(price_min + (i + 1) * bin_size, 4),
            "volume": round(v, 4),
        }
        for i, v in enumerate(bin_volumes)
    ]

    total_volume = sum(bin_volumes)
    if total_volume <= 0:
        return {**empty, "bins": bins}

    poc_idx = max(range(num_bins), key=lambda i: bin_volumes[i])
    poc_price = round((bins[poc_idx]["price_low"] + bins[poc_idx]["price_high"]) / 2, 4)

    # Value area: grow outward from POC, always taking whichever neighbor
    # (above or below the current window) holds more volume, until >= 70%
    # of total volume is included.
    lo_idx, hi_idx = poc_idx, poc_idx
    included = bin_volumes[poc_idx]
    target = total_volume * 0.70
    while included < target and (lo_idx > 0 or hi_idx < num_bins - 1):
        vol_below = bin_volumes[lo_idx - 1] if lo_idx > 0 else -1.0
        vol_above = bin_volumes[hi_idx + 1] if hi_idx < num_bins - 1 else -1.0
        if vol_above >= vol_below:
            hi_idx += 1
            included += bin_volumes[hi_idx]
        else:
            lo_idx -= 1
            included += bin_volumes[lo_idx]

    return {
        "bins": bins,
        "poc_price": poc_price,
        "value_area_high": bins[hi_idx]["price_high"],
        "value_area_low": bins[lo_idx]["price_low"],
    }
