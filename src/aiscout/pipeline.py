"""End-to-end pipeline orchestration (docs/04).

Runs: data -> features -> labels -> leakage-safe walk-forward validation (GBM +
baselines) -> regime-stratified metrics -> locked holdout -> cost-aware backtest ->
final model -> explainable alerts. Emits a results dict consumed by report.py.

The 'continuously thinking' nightly loop is exactly one call to `run()`; in production
it is scheduled after close each day. Here we run it once over history to validate.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config, DEFAULT
from .features import build_features, FEATURE_COLUMNS
from .labeling import build_labels, label_summary
from .validation import walk_forward_folds, make_holdout
from .model import CalibratedGBM, RuleBaseline, LogisticBaseline
from .metrics import evaluate, reliability_curve
from .backtest import run_backtest
from .alerts import build_alerts


def _regime_tag(index_df: pd.DataFrame) -> pd.Series:
    """Bull/Bear/Sideways from the market's 60d return; indexed by date."""
    c = index_df.set_index("date")["close"]
    r60 = c.pct_change(60)
    tag = pd.Series(np.where(r60 > 0.05, "bull",
                    np.where(r60 < -0.05, "bear", "sideways")), index=c.index)
    return tag


def run(panel: pd.DataFrame, index_df: pd.DataFrame, cfg: Config = DEFAULT,
        data_label: str = "SYNTHETIC") -> dict:
    feats = build_features(panel, index_df)
    labeled = build_labels(feats, cfg)
    lab_sum = label_summary(labeled)

    # modeling frame: tradable, labeled, and features present
    df = labeled[labeled["tradable"] & labeled["label"].notna()].copy()
    df = df.dropna(subset=["atr_pct_20"])
    X_all = df[FEATURE_COLUMNS]
    y_all = df["label"].astype(int).to_numpy()
    dates = df["date"]
    regime = _regime_tag(index_df)
    df["regime"] = df["date"].map(regime)

    # ---- walk-forward OOS predictions (GBM + baselines) ----
    oos = np.full(len(df), np.nan)
    oos_rule = np.full(len(df), np.nan)
    oos_logit = np.full(len(df), np.nan)
    pos = df.reset_index(drop=True)

    rule = RuleBaseline()
    for tr_mask, va_mask, _ in walk_forward_folds(dates, cfg.validation,
                                                  cfg.label.horizon_days):
        Xtr, ytr, dtr = X_all[tr_mask], y_all[tr_mask], dates[tr_mask]
        Xva = X_all[va_mask]
        if ytr.sum() < 10:
            continue
        gbm = CalibratedGBM(cfg.model, FEATURE_COLUMNS).fit(Xtr, ytr, dtr)
        oos[va_mask] = gbm.predict_proba(Xva)
        logit = LogisticBaseline().fit(Xtr, ytr)
        oos_logit[va_mask] = logit.predict_proba(Xva)
        oos_rule[va_mask] = rule.predict_proba(Xva)

    pos["p_gbm"], pos["p_rule"], pos["p_logit"] = oos, oos_rule, oos_logit
    # ENSEMBLE: mean of the (decorrelated) calibrated GBM and logistic probabilities.
    with np.errstate(invalid="ignore"):
        stack = np.vstack([oos, oos_logit])
        pos["p_ens"] = np.where(np.isfinite(stack).any(axis=0),
                                np.nanmean(stack, axis=0), np.nan)
    scored = pos[np.isfinite(oos)].copy()

    metrics = {
        "ensemble": evaluate(scored["label"], scored["p_ens"]),
        "gbm": evaluate(scored["label"], scored["p_gbm"]),
        "logistic_baseline": evaluate(scored["label"], scored["p_logit"]),
        "rule_baseline": evaluate(scored["label"], scored["p_rule"]),
    }
    # pick the production scorer = best OOS PR-AUC (selection guarded by locked holdout)
    prod = max(("ensemble", "gbm", "logistic_baseline"),
               key=lambda k: metrics[k]["pr_auc"] if np.isfinite(metrics[k]["pr_auc"]) else -1)
    prod_col = {"ensemble": "p_ens", "gbm": "p_gbm", "logistic_baseline": "p_logit"}[prod]
    reliability = reliability_curve(scored["label"], scored[prod_col])

    # ---- regime-stratified metrics (production scorer) ----
    regime_metrics = {}
    for rg, g in scored.groupby("regime"):
        if len(g) > 50:
            regime_metrics[rg] = evaluate(g["label"], g[prod_col])

    # ---- locked holdout (touched once), scored with the production model ----
    hold_mask, hold_cut = make_holdout(dates, frac=0.2)
    tr = ~hold_mask
    holdout = {"error": "insufficient data"}
    if y_all[tr].sum() > 10 and hold_mask.sum() > 20:
        gbm_h = CalibratedGBM(cfg.model, FEATURE_COLUMNS).fit(
            X_all[tr], y_all[tr], dates[tr])
        p_h = gbm_h.predict_proba(X_all[hold_mask])
        if prod != "gbm":
            logit_h = LogisticBaseline().fit(X_all[tr], y_all[tr])
            p_hl = logit_h.predict_proba(X_all[hold_mask])
            p_h = p_hl if prod == "logistic_baseline" else (p_h + p_hl) / 2
        holdout = evaluate(df.loc[hold_mask, "label"], p_h)
        holdout["cut_date"] = str(pd.to_datetime(hold_cut).date())
        holdout["model"] = prod

    # ---- cost-aware backtest on OOS signals (fire top-k per day) ----
    fired = []
    for d, g in scored.groupby("date"):
        g = g[(g[prod_col] >= cfg.ranking.min_confidence)]
        g = g.sort_values(prod_col, ascending=False).head(cfg.ranking.top_k_per_day)
        for _, r in g.iterrows():
            fired.append({
                "entry_date": r["entry_date"], "exit_date": r["exit_date"],
                "confidence": r["p_gbm"], "ret_realized": r["ret_realized"],
                "amihud_illiq": r.get("amihud_illiq", 0.0), "symbol": r["symbol"],
            })
    fired_df = pd.DataFrame(fired)
    bt = run_backtest(fired_df, cfg) if not fired_df.empty else {"error": "no signals"}

    # ---- final model on ALL data -> alerts for the latest date ----
    final = CalibratedGBM(cfg.model, FEATURE_COLUMNS).fit(X_all, y_all, dates)
    final_logit = LogisticBaseline().fit(X_all, y_all) if prod != "gbm" else None
    last_day = feats["date"].max()
    latest = feats[feats["date"] == last_day].dropna(subset=["atr_pct_20"]).copy()
    latest = latest[latest[FEATURE_COLUMNS].notna().mean(axis=1) > 0.7]
    alerts = []
    if len(latest):
        p_g = final.predict_proba(latest[FEATURE_COLUMNS])
        if prod == "gbm":
            latest["pred_proba"] = p_g
        elif prod == "logistic_baseline":
            latest["pred_proba"] = final_logit.predict_proba(latest[FEATURE_COLUMNS])
        else:
            latest["pred_proba"] = (p_g + final_logit.predict_proba(latest[FEATURE_COLUMNS])) / 2
        latest["tradable_now"] = ~(
            (latest.get("t2t", 0) == 1) | (latest.get("asm", 0) == 1) |
            (latest.get("fno_ban", 0) == 1) | (latest.get("upper_circuit", 0) == 1))
        top = latest[latest["tradable_now"]].sort_values(
            "pred_proba", ascending=False).head(cfg.ranking.top_k_per_day)
        if len(top):
            contrib = final.contributions(top)
            # crude historical-analog stat: base rate of the positive class
            analog = {"n_similar_setups": int(scored.shape[0]),
                      "historical_hit_rate": round(float(scored["label"].mean()), 3)}
            alerts = build_alerts(top, contrib, cfg, analog)

    return {
        "data_label": data_label,
        "production_model": prod,
        "universe": {"symbols": int(panel["symbol"].nunique()),
                     "days": int(panel["date"].nunique()),
                     "date_range": [str(panel["date"].min().date()),
                                    str(panel["date"].max().date())]},
        "label_summary": lab_sum,
        "config": {
            "horizon_days": cfg.label.horizon_days,
            "k_up_atr": cfg.label.k_up_atr, "m_down_atr": cfg.label.m_down_atr,
            "top_k_per_day": cfg.ranking.top_k_per_day,
            "embargo_days": cfg.validation.embargo_days,
        },
        "metrics_oos": metrics,
        "regime_metrics": regime_metrics,
        "reliability": reliability,
        "holdout": holdout,
        "backtest": bt,
        "alerts": alerts,
        "n_features": len(FEATURE_COLUMNS),
    }
