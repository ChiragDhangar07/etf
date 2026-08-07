"""India cash-equity round-trip cost model (docs/03 sec 2.7).

A pre-cost edge is not an edge. Every backtested return passes through here. Costs are
expressed as a fraction of notional and include STT, exchange/SEBI charges, stamp duty,
GST, brokerage, and a liquidity-scaled slippage+impact term.
"""
from __future__ import annotations

from .config import CostConfig


def round_trip_cost_frac(cfg: CostConfig, amihud_illiq: float = 0.0) -> float:
    """Total round-trip cost as a fraction of notional (buy + sell)."""
    brokerage = 2 * cfg.brokerage_per_side
    txn = 2 * cfg.exchange_txn
    sebi = 2 * cfg.sebi_charges
    gst = cfg.gst_on_charges * (brokerage + txn)
    statutory = cfg.stt_sell + cfg.stamp_buy + txn + sebi + gst + brokerage
    # slippage: base per side (x2) plus impact scaled by illiquidity proxy
    slip = 2 * cfg.slippage_bps / 1e4
    impact = cfg.impact_bps_per_illiquidity / 1e4 * min(max(amihud_illiq, 0.0), 5.0)
    return statutory + slip + impact
