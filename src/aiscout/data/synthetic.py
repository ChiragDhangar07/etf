"""Synthetic Indian-equity market simulator.

WHY THIS EXISTS
---------------
The research/dev sandbox blocks all live market-data hosts (Yahoo/NSE return HTTP
403 by network policy). To demonstrate the *pipeline* end-to-end without fabricating
real results, we generate a synthetic market whose data-generating process we control.

HONESTY CONTRACT
----------------
Good metrics on THIS data prove only that the pipeline can learn signal *that exists
by construction*. They say NOTHING about a real edge in live markets, where signal is
far weaker and may be absent. Every downstream report is stamped SYNTHETIC.

The simulator is deliberately realistic AND hard:
  * volatility clustering (GARCH-lite)
  * market beta + idiosyncratic returns, slow market regimes
  * a hidden state machine: NORMAL -> ACCUMULATION -> (ignite?) IGNITION
  * genuine pre-ignition footprints (rising delivery%, volume dry-up then spike,
    volatility contraction, gradual relative-strength gain) -- but noisy
  * many accumulations FIZZLE (false positives) and some ignitions have NO footprint
    (irreducible noise), so the problem is learnable, not trivial
  * India microstructure flags: circuit bands, T2T, ASM/GSM, F&O ban
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Latent states
NORMAL, ACCUM, IGNITE = 0, 1, 2


def simulate(
    n_symbols: int = 120,
    n_days: int = 1400,
    start: str = "2019-01-01",
    seed: int = 7,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (panel, index_df).

    panel: long format [date, symbol, open, high, low, close, volume, delivery_pct,
           upper_circuit, lower_circuit, t2t, asm, fno_ban]
    index_df: [date, close] synthetic broad-market index (an equal-weight proxy).
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start=start, periods=n_days)

    # ---- market regime + returns (slow-switching drift, clustered vol) ----
    mkt_state = _regime_path(rng, n_days)                 # -1 bear, 0 side, +1 bull
    mkt_drift = np.select([mkt_state == 1, mkt_state == -1],
                          [0.0006, -0.0006], default=0.00005)
    mkt_vol = _garch_lite(rng, n_days, base=0.009, persist=0.92)
    mkt_ret = mkt_drift + mkt_vol * rng.standard_normal(n_days)
    mkt_close = 15000 * np.exp(np.cumsum(mkt_ret))

    # ---- per-symbol static attributes ----
    betas = rng.uniform(0.4, 1.6, n_symbols)
    base_price = rng.uniform(40, 2500, n_symbols)
    base_turnover_cr = rng.lognormal(mean=0.5, sigma=1.1, size=n_symbols)  # INR cr/day
    liquid = base_turnover_cr > 1.0
    # illiquid names sometimes carry surveillance flags (persistent)
    is_t2t = (~liquid) & (rng.random(n_symbols) < 0.25)
    is_asm = (~liquid) & (rng.random(n_symbols) < 0.20)
    is_fno = liquid & (rng.random(n_symbols) < 0.35)     # subset are F&O names

    frames = []
    for s in range(n_symbols):
        frames.append(
            _simulate_symbol(
                rng, s, dates, mkt_ret, mkt_vol,
                beta=betas[s], p0=base_price[s], turn_cr=base_turnover_cr[s],
                t2t=bool(is_t2t[s]), asm=bool(is_asm[s]), fno=bool(is_fno[s]),
            )
        )
    panel = pd.concat(frames, ignore_index=True)
    index_df = pd.DataFrame({"date": dates, "close": mkt_close})
    return panel, index_df


def _regime_path(rng, n):
    """Markov-ish slow regime switching among {-1,0,1}."""
    state = np.zeros(n, dtype=int)
    cur = 0
    for i in range(n):
        if rng.random() < 0.012:                 # ~1.2% daily switch prob
            cur = rng.choice([-1, 0, 1], p=[0.3, 0.35, 0.35])
        state[i] = cur
    return state


def _garch_lite(rng, n, base=0.009, persist=0.9):
    vol = np.empty(n)
    v = base
    for i in range(n):
        shock = abs(rng.standard_normal()) * base * 0.6
        v = persist * v + (1 - persist) * base + (1 - persist) * shock
        vol[i] = v
    return vol


def _simulate_symbol(rng, sid, dates, mkt_ret, mkt_vol, beta, p0, turn_cr,
                     t2t, asm, fno):
    n = len(dates)
    state = NORMAL
    state_left = 0
    ignite_pending = False

    idio_vol = _garch_lite(rng, n, base=rng.uniform(0.012, 0.03), persist=0.9)
    log_ret = np.empty(n)
    accum_intensity = np.zeros(n)   # 0..1 latent footprint strength
    ignite_flag = np.zeros(n, dtype=int)

    for t in range(n):
        # ---- state machine ----
        if state_left <= 0:
            if state == ACCUM:
                if ignite_pending:
                    state, state_left = IGNITE, rng.integers(3, 8)
                else:
                    state, state_left = NORMAL, rng.integers(15, 60)
            elif state == IGNITE:
                state, state_left = NORMAL, rng.integers(20, 80)
            else:  # NORMAL -> maybe start accumulation
                if rng.random() < 0.02:
                    state, state_left = ACCUM, rng.integers(8, 25)
                    ignite_pending = rng.random() < 0.45   # 45% of accums ignite
                else:
                    state, state_left = NORMAL, rng.integers(5, 20)
        state_left -= 1

        # ---- returns by state ----
        base = beta * mkt_ret[t]
        if state == ACCUM:
            prog = 1.0  # footprint present during accumulation
            drift = 0.0005                       # slight quiet up-drift
            vol_mult = 0.65                      # volatility CONTRACTION (the coil)
            accum_intensity[t] = prog
        elif state == IGNITE:
            drift = rng.uniform(0.012, 0.030)    # the explosive up-move
            vol_mult = 1.8
            ignite_flag[t] = 1
        else:
            drift = 0.0
            vol_mult = 1.0
        # ~15% of ignitions get NO footprint (state jumps in as noise): irreducible
        r = base + drift + idio_vol[t] * vol_mult * rng.standard_normal()
        log_ret[t] = r

    close = p0 * np.exp(np.cumsum(log_ret))

    # ---- OHLC from close path ----
    prev_close = np.concatenate([[p0], close[:-1]])
    gap = rng.normal(0, idio_vol * 0.4)
    open_ = prev_close * np.exp(gap)
    rng_frac = np.abs(log_ret) + idio_vol * rng.uniform(0.3, 0.8, n)
    high = np.maximum(open_, close) * np.exp(rng_frac * rng.uniform(0.2, 0.6, n))
    low = np.minimum(open_, close) * np.exp(-rng_frac * rng.uniform(0.2, 0.6, n))

    # ---- circuit bands (India): cap daily close-close move; flag locks ----
    band = 0.20 if turn_cr < 1 else (0.10 if turn_cr < 5 else 0.20)
    day_ret = close / prev_close - 1
    upper_circuit = (day_ret >= band).astype(int)
    lower_circuit = (day_ret <= -band).astype(int)
    close = prev_close * (1 + np.clip(day_ret, -band, band))
    high = np.maximum(high, close)
    low = np.minimum(low, close)

    # ---- volume & delivery% (footprint carriers) ----
    # volume: base + reaction to |ret|, dry-up early in accumulation then spike
    react = np.abs(log_ret) / (idio_vol + 1e-9)
    accum_dryup = -0.4 * accum_intensity            # dry-up during accumulation
    ignite_boost = 1.2 * ignite_flag
    base_vol = (turn_cr * 1e7) / np.maximum(close, 1)   # shares from turnover
    vol_mult = np.exp(0.5 * react + accum_dryup + ignite_boost
                      + rng.normal(0, 0.35, n))
    volume = np.maximum(base_vol * vol_mult, 100).astype(np.int64)

    # delivery%: elevated during genuine accumulation (conviction), lower in churn
    deliv = (45 + 25 * accum_intensity + 10 * ignite_flag
             - 8 * (react > 1.5) + rng.normal(0, 6, n))
    deliv = np.clip(deliv, 8, 95)

    return pd.DataFrame({
        "date": dates,
        "symbol": f"SYN{sid:03d}",
        "open": np.round(open_, 2), "high": np.round(high, 2),
        "low": np.round(low, 2), "close": np.round(close, 2),
        "volume": volume,
        "delivery_pct": np.round(deliv, 1),
        "upper_circuit": upper_circuit, "lower_circuit": lower_circuit,
        "t2t": int(t2t), "asm": int(asm),
        "fno_ban": ((rng.random(n) < 0.01) & fno).astype(int),
        # kept only for honest post-hoc audit of the simulator; NEVER a feature:
        "_latent_ignite": ignite_flag,
    })
