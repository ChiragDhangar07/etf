"""Leakage-safe walk-forward validation (docs/03 sec 2).

Financial ML fails mostly through leakage, not weak models. This module enforces:
  * TIME-ORDERED splits (train strictly precedes validation) -- walk-forward.
  * PURGING: training samples whose label window overlaps the validation window are
    removed (overlapping H-day triple-barrier labels would otherwise leak).
  * EMBARGO: a buffer of `embargo_days` after each validation block is dropped from
    training so information does not bleed across the boundary.
A final most-recent block is reserved as a locked out-of-sample holdout by the caller.

Implementation note: dates are mapped to integer codes (0..D-1 over sorted unique
trading days) so all masking is fast integer comparison -- never np.isin over datetime
objects, which silently falls back to O(n*m) elementwise Python comparisons.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ValidationConfig


def _date_codes(dates: pd.Series):
    uniq = np.array(sorted(dates.unique()))
    code_map = {d: i for i, d in enumerate(uniq)}
    codes = dates.map(code_map).to_numpy()
    return uniq, codes


def walk_forward_folds(dates: pd.Series, cfg: ValidationConfig, horizon: int):
    """Yield (train_mask, valid_mask, valid_start_date) over unique sorted dates.

    Expanding train window; each subsequent contiguous date block is a validation fold.
    Purge + embargo applied around each validation block.
    `dates` is a per-sample Series of the sample's decision date (day t).
    """
    uniq, codes = _date_codes(dates)
    n = len(uniq)
    start = cfg.min_train_days
    if start >= n:
        start = max(int(n * 0.5), 1)
    remaining = n - start
    fold_len = max(remaining // cfg.n_splits, 1)

    for i in range(cfg.n_splits):
        v_lo = start + i * fold_len
        v_hi = n if i == cfg.n_splits - 1 else start + (i + 1) * fold_len
        if v_lo >= n:
            break
        # PURGE + EMBARGO: training labels must finish before validation starts, minus
        # (horizon + embargo) days.
        purge_cut = max(v_lo - horizon - cfg.embargo_days, 0)
        train_mask = codes < purge_cut
        valid_mask = (codes >= v_lo) & (codes < v_hi)
        if train_mask.sum() == 0 or valid_mask.sum() == 0:
            continue
        yield train_mask, valid_mask, uniq[v_lo]


def make_holdout(dates: pd.Series, frac: float = 0.2):
    """Return (holdout_mask, cut_date): the most-recent `frac` of dates as holdout."""
    uniq, codes = _date_codes(dates)
    cut_code = int(len(uniq) * (1 - frac))
    return codes >= cut_code, uniq[cut_code]
