"""Explainable alert generation (docs/04 alert schema).

An alert is never a bare 'buy'. Each carries: calibrated probability, confidence,
top reasons (from GBM feature contributions), supporting evidence, risk factors,
invalidation level, expected timeframe, historical-analog stats, suggested size, and
tradability status.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config

# Human-readable phrasing for the biggest positive contributors
_REASONS = {
    "xs_rvol_rank": "Abnormally high relative volume vs the market",
    "rvol_20": "Volume surge vs its own 20-day average",
    "breakout_20": "Closed above its prior 20-day high (breakout)",
    "delivery_trend": "Delivery% rising vs 20-day mean (accumulation)",
    "delivery_pct": "High delivery% (conviction, not churn)",
    "vol_contraction": "Volatility contracted into a coil",
    "bb_width_pctile": "Bollinger width compressed (energy stored)",
    "xs_rs_rank": "Strong relative strength vs peers",
    "rs_ret_20": "Outperforming the market over 20 days",
    "rs_slope_10": "Relative strength accelerating",
    "dist_20d_high": "Trading near its 20-day high",
    "dist_52w_high": "Trading near its 52-week high",
    "up_streak": "Sustained up-day streak",
    "anomaly_z": "Behaving statistically unusually vs its own history",
    "obs_slope_10": "On-balance-volume trending up (accumulation)",
}


def build_alerts(latest: pd.DataFrame, contrib: pd.DataFrame, cfg: Config,
                 analog_stats: dict | None = None) -> list[dict]:
    alerts = []
    feat_cols = [c for c in contrib.columns if c != "_bias"]
    for idx, row in latest.iterrows():
        c = contrib.loc[idx, feat_cols].sort_values(ascending=False)
        top_pos = [(k, _REASONS.get(k, k)) for k in c.index[:4] if c[k] > 0]
        top_neg = [k for k in c.index[-3:] if c[k] < 0]

        atr = float(row.get("atr_pct_20", np.nan))
        price = float(row["close"])
        conf = float(row["pred_proba"])
        # invalidation: stop level from the labeling scheme
        stop = price * (1 - cfg.label.m_down_atr * atr) if np.isfinite(atr) else np.nan
        target = price * (1 + cfg.label.k_up_atr * atr) if np.isfinite(atr) else np.nan
        rr = (cfg.label.k_up_atr / cfg.label.m_down_atr) if atr else np.nan

        risks = []
        if row.get("near_upper_circuit", 0) >= 1:
            risks.append("Near/at upper circuit — entry fills may be hard")
        if row.get("amihud_illiq", 0) and row["amihud_illiq"] > 1:
            risks.append("Elevated illiquidity — slippage/impact risk")
        if row.get("t2t", 0) == 1:
            risks.append("T2T segment — delivery-only, no intraday")

        alerts.append({
            "symbol": row["symbol"],
            "date": str(pd.to_datetime(row["date"]).date()),
            "price": round(price, 2),
            "signal_type": "swing-upside-explosion",
            "probability": round(conf, 3),
            "confidence": round(conf, 3),
            "expected_timeframe_days": cfg.label.horizon_days,
            "target": round(target, 2) if np.isfinite(target) else None,
            "stop_invalidation": round(stop, 2) if np.isfinite(stop) else None,
            "expected_reward_risk": round(rr, 2) if rr else None,
            "expected_move_pct": round(cfg.label.k_up_atr * atr * 100, 1) if np.isfinite(atr) else None,
            "reasons": [r for _, r in top_pos],
            "risk_factors": risks or ["No standout microstructure risk flagged"],
            "suggested_size_frac": round(min(conf, 1.0) / cfg.ranking.top_k_per_day, 4),
            "historical_analogs": analog_stats or {},
            "tradable": bool(row.get("tradable_now", True)),
        })
    return alerts
