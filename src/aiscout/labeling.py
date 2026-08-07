"""Triple-barrier labeling with India tradability gate (docs/00).

For each candidate day t:
  * entry at day t+1 OPEN (no look-ahead). If entry is blocked (t+1 opens locked at
    upper circuit, or the name is T2T / ASM / in F&O ban at t) the sample is dropped
    (label = NaN) -- an untradable prediction is not a win (risk R4).
  * upper barrier = entry * (1 + k * ATR%20_t)   -> label 1 (explosive)
  * lower barrier = entry * (1 - m * ATR%20_t)    -> label 0 (stopped)
  * vertical barrier at t+H                        -> label 0 (no move / timeout)
Label is set by whichever barrier is touched first (path-dependent). When both the
upper and lower barrier fall inside the same day's range, we CONSERVATIVELY assume the
stop was hit first (pessimistic -> avoids optimistic labeling bias).

Also emits realized-trade fields used by the cost-aware backtest.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config, DEFAULT


def _label_symbol(g: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    g = g.sort_values("date").reset_index(drop=True)
    n = len(g)
    lc = cfg.label
    high = g["high"].to_numpy()
    low = g["low"].to_numpy()
    open_ = g["open"].to_numpy()
    atrp = g["atr_pct_20"].to_numpy()
    up_circ = g.get("upper_circuit", pd.Series(np.zeros(n))).to_numpy()
    t2t = g.get("t2t", pd.Series(np.zeros(n))).to_numpy()
    asm = g.get("asm", pd.Series(np.zeros(n))).to_numpy()
    ban = g.get("fno_ban", pd.Series(np.zeros(n))).to_numpy()

    dates = g["date"].to_numpy()
    label = np.full(n, np.nan)
    entry_price = np.full(n, np.nan)
    exit_price = np.full(n, np.nan)
    exit_idx = np.full(n, -1)
    entry_date = np.full(n, np.datetime64("NaT"), dtype="datetime64[ns]")
    exit_date = np.full(n, np.datetime64("NaT"), dtype="datetime64[ns]")
    barrier = np.array([""] * n, dtype=object)
    tradable = np.zeros(n, dtype=bool)

    H = lc.horizon_days
    for t in range(n - H - 1):
        if not np.isfinite(atrp[t]) or atrp[t] <= 0:
            continue
        e = t + 1  # entry day (next open)
        # tradability gate at entry
        blocked = (
            (cfg.universe.exclude_upper_circuit_entry and up_circ[e] == 1) or
            (cfg.universe.exclude_t2t and t2t[t] == 1) or
            (cfg.universe.exclude_asm_gsm and asm[t] == 1) or
            (cfg.universe.exclude_fno_ban and ban[t] == 1)
        )
        if blocked:
            continue
        entry = open_[e]
        if not np.isfinite(entry) or entry <= 0:
            continue
        up = entry * (1 + lc.k_up_atr * atrp[t])
        dn = entry * (1 - lc.m_down_atr * atrp[t])
        entry_price[t] = entry
        tradable[t] = True

        lab, bxr, xidx, xpx = 0, "time", min(e + H, n - 1), np.nan
        for d in range(e, min(e + H + 1, n)):
            hit_up = high[d] >= up
            hit_dn = low[d] <= dn
            if hit_dn:            # conservative: stop first if both
                lab, bxr, xidx, xpx = 0, "down", d, dn
                break
            if hit_up:
                lab, bxr, xidx, xpx = 1, "up", d, up
                break
        if bxr == "time":
            xpx = g["close"].to_numpy()[xidx]
        label[t] = lab
        barrier[t] = bxr
        exit_idx[t] = xidx
        exit_price[t] = xpx
        entry_date[t] = dates[e]
        exit_date[t] = dates[xidx]

    g["label"] = label
    g["entry_price"] = entry_price
    g["exit_price"] = exit_price
    g["exit_idx"] = exit_idx
    g["entry_date"] = entry_date
    g["exit_date"] = exit_date
    g["barrier"] = barrier
    g["tradable"] = tradable
    g["ret_realized"] = exit_price / entry_price - 1
    return g


def build_labels(feat_panel: pd.DataFrame, cfg: Config = DEFAULT) -> pd.DataFrame:
    out = pd.concat([_label_symbol(g, cfg) for _, g in feat_panel.groupby("symbol")],
                    ignore_index=True)
    return out


def label_summary(panel: pd.DataFrame) -> dict:
    lab = panel.loc[panel["tradable"], "label"].dropna()
    return {
        "labeled_samples": int(lab.shape[0]),
        "positive_rate": float(lab.mean()) if len(lab) else float("nan"),
        "n_positive": int(lab.sum()),
    }
