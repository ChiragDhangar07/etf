"""Leakage-safe walk-forward validation (docs/03 sec 2).

Financial ML fails mostly through leakage, not weak models. This module enforces:
  * TIME-ORDERED splits (train strictly precedes validation) -- walk-forward.
  * PURGING: training samples whose label window overlaps the validation window are
    removed (overlapping H-day triple-barrier labels would otherwise leak).
  * EMBARGO: a buffer of `embargo_days` after each validation block is dropped from
    training so information does not bleed across the boundary.
A final most-recent block is reserved as a locked out-of-sample holdout by the caller.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ValidationConfig


def walk_forward_folds(dates: pd.Series, cfg: ValidationConfig, horizon: int):
    """Yield (train_mask, valid_mask) over unique sorted dates.

    Expanding train window; each subsequent contiguous date block is a validation fold.
    Purge + embargo applied around each validation block.
    `dates` is a per-sample Series of the sample's decision date (day t).
    """
    uniq = np.array(sorted(dates.unique()))
    n = len(uniq)
    start = cfg.min_train_days
    if start >= n:
        start = max(int(n * 0.5), 1)
    remaining = n - start
    fold_len = max(remaining // cfg.n_splits, 1)

    date_arr = dates.to_numpy()
    for i in range(cfg.n_splits):
        v_lo = start + i * fold_len
        v_hi = n if i == cfg.n_splits - 1 else start + (i + 1) * fold_len
        if v_lo >= n:
            break
        valid_dates = set(uniq[v_lo:v_hi])
        valid_start = uniq[v_lo]
        # PURGE: training labels must finish before validation starts, minus horizon.
        # EMBARGO: also drop `embargo_days` of dates before validation start.
        purge_cut_idx = max(v_lo - horizon - cfg.embargo_days, 0)
        train_dates = set(uniq[:purge_cut_idx])

        train_mask = np.isin(date_arr, list(train_dates))
        valid_mask = np.isin(date_arr, list(valid_dates))
        if train_mask.sum() == 0 or valid_mask.sum() == 0:
            continue
        yield train_mask, valid_mask, valid_start


def make_holdout(dates: pd.Series, frac: float = 0.2):
    """Return a boolean mask marking the most-recent `frac` of dates as holdout."""
    uniq = np.array(sorted(dates.unique()))
    cut = uniq[int(len(uniq) * (1 - frac))]
    return dates.to_numpy() >= cut, cut
