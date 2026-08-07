"""Cost-aware portfolio backtest (docs/03 sec 2.7).

A simplified but fully-specified swing portfolio:
  * Each fired signal is a trade with a known entry date, exit date, and realized
    triple-barrier return (path-dependent, already stop/target-aware).
  * At most `max_concurrent` positions are held at once (a real capital constraint);
    excess same-day signals are skipped in rank order.
  * Each trade is allocated a fixed fraction f = 1/max_concurrent of current equity at
    entry; its PnL (net of the full India cost model, illiquidity-scaled) is credited to
    equity at exit. Equity compounds.
This is intentionally conservative and transparent -- no intraday MTM leverage, no
optimistic fills. Returns reported here are SYNTHETIC-data results: they validate the
machinery, not a live edge.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config
from .costs import round_trip_cost_frac


def run_backtest(signals: pd.DataFrame, cfg: Config, max_concurrent: int = 10) -> dict:
    """signals: one row per fired trade with columns
       [entry_date, exit_date, confidence, ret_realized, amihud_illiq, symbol]."""
    if signals.empty:
        return {"error": "no signals"}
    s = signals.sort_values("entry_date").reset_index(drop=True)
    f = 1.0 / max_concurrent

    # net return after costs, per trade
    cost = s["amihud_illiq"].fillna(0).apply(
        lambda a: round_trip_cost_frac(cfg.cost, a)
    )
    s["ret_net"] = s["ret_realized"].fillna(0) - cost

    all_dates = pd.Index(sorted(set(s["entry_date"]) | set(s["exit_date"])))
    equity = 1.0
    open_pos: list[dict] = []
    trade_rets, curve, curve_dates = [], [], []

    entries_by_date = {d: g for d, g in s.groupby("entry_date")}

    for d in all_dates:
        # 1) process exits
        still = []
        for p in open_pos:
            if p["exit_date"] <= d:
                pnl = p["alloc"] * p["ret_net"]
                equity += pnl
                trade_rets.append(p["ret_net"])
            else:
                still.append(p)
        open_pos = still
        # 2) process entries (rank order already applied upstream)
        if d in entries_by_date:
            for _, row in entries_by_date[d].iterrows():
                if len(open_pos) >= max_concurrent:
                    break
                open_pos.append({
                    "exit_date": row["exit_date"],
                    "alloc": f * equity,
                    "ret_net": row["ret_net"],
                })
        curve.append(equity)
        curve_dates.append(d)

    curve = pd.Series(curve, index=curve_dates)
    daily = curve.pct_change().dropna()
    trade_rets = np.array(trade_rets)
    wins = trade_rets[trade_rets > 0]
    losses = trade_rets[trade_rets <= 0]
    span_years = max((all_dates[-1] - all_dates[0]).days / 365.25, 1e-6)

    return {
        "n_trades": int(len(trade_rets)),
        "total_return": float(curve.iloc[-1] - 1),
        "cagr": float(curve.iloc[-1] ** (1 / span_years) - 1),
        "sharpe": float(daily.mean() / (daily.std() + 1e-12) * np.sqrt(252)) if len(daily) > 5 else float("nan"),
        "max_drawdown": float((curve / curve.cummax() - 1).min()),
        "hit_rate": float((trade_rets > 0).mean()) if len(trade_rets) else float("nan"),
        "avg_win": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss": float(losses.mean()) if len(losses) else 0.0,
        "profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else float("inf"),
        "avg_trade_net": float(trade_rets.mean()) if len(trade_rets) else float("nan"),
        "equity_curve": {"dates": [str(x.date()) for x in curve.index],
                         "equity": [float(x) for x in curve.values]},
    }
