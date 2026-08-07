"""Models: rule + logistic baselines and a calibrated GBM (docs/03).

Design principles enforced here:
  * SIMPLE BEFORE COMPLEX -- the GBM must beat the baselines out-of-sample to earn its
    place. Both baselines are first-class citizens, not throwaways.
  * CALIBRATION IS MANDATORY -- raw tree probabilities are not trustworthy. We fit an
    isotonic map on a TIME-ORDERED tail of the training data (never on the future).
  * EXPLAINABILITY -- the GBM exposes per-prediction feature contributions
    (LightGBM `pred_contrib`) so every alert can state WHY (docs/04 alert schema).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.impute import SimpleImputer

from .config import ModelConfig


class RuleBaseline:
    """Transparent domain-prior score: RVOL + breakout + delivery conviction +
    volatility contraction + relative strength. Zero fitting -> zero overfit.
    Encodes the classic swing setup: a quiet coil under accumulation that ignites."""

    RULES = {
        "xs_rvol_rank": 1.0,
        "breakout_20": 1.0,
        "delivery_trend": 0.05,
        "vol_contraction": -0.8,   # lower contraction ratio = tighter coil = bullish
        "xs_rs_rank": 1.0,
        "dist_20d_high": 2.0,      # closer to highs (less negative) = better
    }

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        z = np.zeros(len(X))
        for col, w in self.RULES.items():
            if col in X:
                x = X[col].astype(float)
                x = (x - x.mean()) / (x.std() + 1e-9)
                z += w * x.fillna(0).to_numpy()
        return 1 / (1 + np.exp(-(z - z.mean()) / (z.std() + 1e-9)))


class LogisticBaseline:
    def __init__(self):
        self.imp = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.clf = LogisticRegression(max_iter=1000, class_weight="balanced", C=0.5)

    def fit(self, X, y):
        Xt = self.scaler.fit_transform(self.imp.fit_transform(X))
        self.clf.fit(Xt, y)
        return self

    def predict_proba(self, X):
        Xt = self.scaler.transform(self.imp.transform(X))
        return self.clf.predict_proba(Xt)[:, 1]


class CalibratedGBM:
    """LightGBM primary model + isotonic calibration on a time-ordered tail."""

    def __init__(self, cfg: ModelConfig, feature_names, calib_tail: float = 0.2):
        self.cfg = cfg
        self.features = list(feature_names)
        self.calib_tail = calib_tail
        self.model: LGBMClassifier | None = None
        self.calibrator: IsotonicRegression | None = None

    def fit(self, X: pd.DataFrame, y, dates: pd.Series):
        order = np.argsort(dates.to_numpy())
        X = X.iloc[order]
        y = np.asarray(y)[order]
        cut = int(len(X) * (1 - self.calib_tail))
        Xtr, ytr = X.iloc[:cut], y[:cut]
        Xca, yca = X.iloc[cut:], y[cut:]

        pos = max(ytr.sum(), 1)
        neg = max(len(ytr) - pos, 1)
        params = dict(self.cfg.lgbm_params)
        params["scale_pos_weight"] = float(neg / pos)  # counter imbalance

        self.model = LGBMClassifier(**params)
        self.model.fit(Xtr[self.features], ytr)

        if len(Xca) > 30 and 0 < yca.sum() < len(yca):
            raw = self.model.predict_proba(Xca[self.features])[:, 1]
            self.calibrator = IsotonicRegression(out_of_bounds="clip").fit(raw, yca)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raw = self.model.predict_proba(X[self.features])[:, 1]
        if self.calibrator is not None:
            return self.calibrator.transform(raw)
        return raw

    def contributions(self, X: pd.DataFrame) -> pd.DataFrame:
        """Per-row feature contributions (log-odds space) for explainable alerts."""
        contrib = self.model.predict_proba(X[self.features], pred_contrib=True)
        cols = self.features + ["_bias"]
        return pd.DataFrame(contrib, columns=cols, index=X.index)
