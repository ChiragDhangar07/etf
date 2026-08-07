"""Feature engine (docs/02).

Computes point-in-time features from a long OHLCV+delivery panel and a market index.
STRICT RULE: every feature at row (symbol, date=t) uses only information available at
or before the close of day t. No feature may reference t+1. Look-ahead here would
silently invalidate the entire project (risk R1).

Features are grouped: momentum/price-action, volatility structure, volume/participation,
relative strength, liquidity/microstructure proxies, delivery (India edge), and
cross-sectional daily ranks. Non-F&O names get NaN options features (handled by the
model natively).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Columns the model may consume. Kept explicit so nothing leaks in by accident.
FEATURE_COLUMNS = [
    # momentum / price action
    "ret_1", "ret_3", "ret_5", "ret_10", "ret_20",
    "dist_20d_high", "dist_52w_high", "breakout_20", "gap_pct",
    "up_streak", "close_pos",
    # volatility structure
    "atr_pct_20", "vol_contraction", "bb_width_pctile",
    # volume / participation
    "rvol_20", "obv_slope_10", "vol_dryup_then_spike",
    # delivery (India edge)
    "delivery_pct", "delivery_trend",
    # relative strength
    "rs_ret_20", "rs_slope_10",
    # liquidity / microstructure proxies
    "turnover_cr", "amihud_illiq", "near_upper_circuit",
    # anomaly
    "anomaly_z",
    # cross-sectional daily ranks
    "xs_ret20_rank", "xs_rvol_rank", "xs_rs_rank",
]


def _true_range(df):
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr


def _per_symbol(df: pd.DataFrame, mkt: pd.Series) -> pd.DataFrame:
    df = df.sort_values("date").copy()
    c, h, l, o, v = df["close"], df["high"], df["low"], df["open"], df["volume"]

    # momentum
    for k in (1, 3, 5, 10, 20):
        df[f"ret_{k}"] = c.pct_change(k)
    roll_high_20 = h.rolling(20).max()
    df["dist_20d_high"] = c / roll_high_20 - 1
    df["dist_52w_high"] = c / h.rolling(252, min_periods=60).max() - 1
    df["breakout_20"] = (c > roll_high_20.shift(1)).astype(float)
    df["gap_pct"] = o / c.shift(1) - 1
    up = (c > c.shift(1)).astype(int)
    # consecutive up-day streak
    grp = (up != up.shift()).cumsum()
    df["up_streak"] = up.groupby(grp).cumsum() * up
    rng = (h - l).replace(0, np.nan)
    df["close_pos"] = ((c - l) / rng).clip(0, 1)

    # volatility structure
    tr = _true_range(df)
    df["atr_pct_20"] = tr.rolling(20).mean() / c
    r1 = c.pct_change()
    df["vol_contraction"] = r1.rolling(5).std() / r1.rolling(20).std()
    bb_width = 2 * r1.rolling(20).std()
    df["bb_width_pctile"] = bb_width.rolling(120, min_periods=40).rank(pct=True)

    # volume / participation
    df["rvol_20"] = v / v.rolling(20).mean()
    obv = (np.sign(c.diff()).fillna(0) * v).cumsum()
    df["obv_slope_10"] = (obv - obv.shift(10)) / v.rolling(20).mean().replace(0, np.nan)
    vol_ma5 = v.rolling(5).mean()
    df["vol_dryup_then_spike"] = (v / vol_ma5.shift(3)) * (vol_ma5.shift(3) /
                                                           v.rolling(20).mean())

    # delivery (India edge) -- may be NaN on non-bhavcopy sources
    if "delivery_pct" in df:
        df["delivery_trend"] = df["delivery_pct"] - df["delivery_pct"].rolling(20).mean()
    else:
        df["delivery_pct"] = np.nan
        df["delivery_trend"] = np.nan

    # relative strength vs market
    mkt_aligned = df["date"].map(mkt)
    df["rs_ret_20"] = (c / c.shift(20)) / (mkt_aligned / mkt_aligned.shift(20)) - 1
    df["rs_slope_10"] = df["rs_ret_20"] - df["rs_ret_20"].shift(10)

    # liquidity / microstructure proxies
    df["turnover_cr"] = c * v / 1e7
    df["amihud_illiq"] = r1.abs() / df["turnover_cr"].replace(0, np.nan)
    band_proxy = df.get("upper_circuit", pd.Series(0, index=df.index))
    df["near_upper_circuit"] = (r1 > 0.08).astype(float) + band_proxy

    # simple anomaly: mean |z| of a few features over own 60d history
    az = []
    for col in ("rvol_20", "ret_5", "delivery_trend", "vol_contraction"):
        x = df[col]
        z = (x - x.rolling(60, min_periods=20).mean()) / x.rolling(60, min_periods=20).std()
        az.append(z.abs())
    df["anomaly_z"] = pd.concat(az, axis=1).mean(axis=1)

    return df


def build_features(panel: pd.DataFrame, index_df: pd.DataFrame) -> pd.DataFrame:
    """Return panel with FEATURE_COLUMNS added. Point-in-time safe."""
    mkt = index_df.set_index("date")["close"]
    # explicit iteration: groupby.apply drops the grouping column in recent pandas
    out = pd.concat([_per_symbol(g, mkt) for _, g in panel.groupby("symbol")],
                    ignore_index=True)

    # cross-sectional daily ranks (relative standing within the universe that day)
    out["xs_ret20_rank"] = out.groupby("date")["ret_20"].rank(pct=True)
    out["xs_rvol_rank"] = out.groupby("date")["rvol_20"].rank(pct=True)
    out["xs_rs_rank"] = out.groupby("date")["rs_ret_20"].rank(pct=True)

    return out.reset_index(drop=True)
