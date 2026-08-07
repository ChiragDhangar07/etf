"""Global configuration for AIScout.

Every tunable that affects labels, universe, costs, or validation lives here so
experiments are reproducible and the point-in-time contract is auditable. Numbers
marked PLACEHOLDER are to be replaced by the Phase-1 empirical move-distribution
study (see docs/00) once real data is available; they are sensible defaults, not
validated truths.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LabelConfig:
    """Triple-barrier labeling (docs/00)."""
    horizon_days: int = 10          # vertical barrier H (<= 10 trading days)
    k_up_atr: float = 2.5           # PLACEHOLDER upper barrier = k * ATR%20  -> explosive
    m_down_atr: float = 1.5         # PLACEHOLDER lower barrier = m * ATR%20  -> stop
    atr_window: int = 20
    entry: str = "next_open"        # trade entered at next day's open (no look-ahead)


@dataclass(frozen=True)
class UniverseConfig:
    """Point-in-time tradability / liquidity floor (docs/00 sec 3, U3)."""
    min_price: float = 20.0                 # PLACEHOLDER
    min_median_turnover_cr: float = 1.0     # PLACEHOLDER median 20d turnover, INR crore
    turnover_window: int = 20
    # Tradability gates: names untradeable at entry are excluded from labels + alerts.
    exclude_upper_circuit_entry: bool = True
    exclude_t2t: bool = True
    exclude_asm_gsm: bool = True
    exclude_fno_ban: bool = True


@dataclass(frozen=True)
class CostConfig:
    """India cash-equity round-trip cost model (docs/03 sec 2.7). Delivery-based swing.

    Rates are representative retail-delivery values; tune to your broker. All in
    fraction of turnover unless noted.
    """
    stt_sell: float = 0.001            # 0.1% on sell (delivery)
    exchange_txn: float = 0.0000297    # ~NSE txn charge
    sebi_charges: float = 0.000001     # SEBI turnover fee
    stamp_buy: float = 0.00015         # 0.015% on buy
    gst_on_charges: float = 0.18       # GST on (brokerage + txn charges)
    brokerage_per_side: float = 0.0    # discount broker delivery often 0
    slippage_bps: float = 15.0         # PLACEHOLDER per side; scaled up for illiquid names
    impact_bps_per_illiquidity: float = 10.0  # extra slippage scaling by Amihud proxy


@dataclass(frozen=True)
class ValidationConfig:
    """Leakage-safe walk-forward (docs/03 sec 2)."""
    n_splits: int = 5
    embargo_days: int = 10             # >= horizon to prevent overlap leakage
    min_train_days: int = 250          # ~1 trading year before first validation
    calibrate: str = "isotonic"        # isotonic | sigmoid | none


@dataclass(frozen=True)
class ModelConfig:
    lgbm_params: dict = field(default_factory=lambda: {
        "objective": "binary",
        "n_estimators": 300,
        "learning_rate": 0.03,
        "num_leaves": 31,
        "max_depth": -1,
        "min_child_samples": 60,
        "subsample": 0.8,
        "subsample_freq": 1,
        "colsample_bytree": 0.8,
        "reg_lambda": 1.0,
        "random_state": 7,
        "n_jobs": -1,
        "verbose": -1,
    })


@dataclass(frozen=True)
class RankingConfig:
    top_k_per_day: int = 5             # alerts/positions surfaced per day
    min_confidence: float = 0.15       # floor on calibrated probability to fire


@dataclass(frozen=True)
class Config:
    label: LabelConfig = field(default_factory=LabelConfig)
    universe: UniverseConfig = field(default_factory=UniverseConfig)
    cost: CostConfig = field(default_factory=CostConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    ranking: RankingConfig = field(default_factory=RankingConfig)
    seed: int = 7


DEFAULT = Config()
