"""Evaluation metrics tuned for a rare-event, precision-oriented problem (docs/00 sec5).

Accuracy is deliberately absent -- it is misleading under heavy class imbalance. We use
PR-AUC, precision@K, Brier score, and reliability-curve data (calibration).
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss


def evaluate(y_true, p_pred, k_frac: float = 0.1) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    p = np.asarray(p_pred, dtype=float)
    m = np.isfinite(y_true) & np.isfinite(p)
    y_true, p = y_true[m], p[m]
    if len(y_true) == 0 or y_true.sum() == 0 or y_true.sum() == len(y_true):
        return {"n": int(len(y_true)), "base_rate": float(y_true.mean()) if len(y_true) else float("nan"),
                "pr_auc": float("nan"), "roc_auc": float("nan"), "brier": float("nan"),
                "precision_at_k": float("nan"), "lift_at_k": float("nan"), "k_frac": k_frac}
    base = float(y_true.mean())
    k = max(int(len(p) * k_frac), 1)
    top_idx = np.argsort(-p)[:k]
    prec_k = float(y_true[top_idx].mean())
    return {
        "n": int(len(y_true)),
        "base_rate": base,
        "pr_auc": float(average_precision_score(y_true, p)),
        "roc_auc": float(roc_auc_score(y_true, p)),
        "brier": float(brier_score_loss(y_true, p)),
        "precision_at_k": prec_k,
        "lift_at_k": float(prec_k / base) if base > 0 else float("nan"),
        "k_frac": k_frac,
    }


def reliability_curve(y_true, p_pred, n_bins: int = 10):
    y_true = np.asarray(y_true, dtype=float)
    p = np.asarray(p_pred, dtype=float)
    m = np.isfinite(y_true) & np.isfinite(p)
    y_true, p = y_true[m], p[m]
    bins = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(p, bins) - 1, 0, n_bins - 1)
    xs, ys, ns = [], [], []
    for b in range(n_bins):
        sel = idx == b
        if sel.sum() == 0:
            continue
        xs.append(float(p[sel].mean()))
        ys.append(float(y_true[sel].mean()))
        ns.append(int(sel.sum()))
    return {"pred": xs, "obs": ys, "count": ns}
