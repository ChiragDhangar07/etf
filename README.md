# AIScout — AI Stock Opportunity Detection (India, swing)

An institutional-grade research system that detects **high-probability upside
"explosive" moves (2–10 trading days) in Indian NSE/BSE cash equities**, emits
**calibrated probabilities with reasoning**, and is built to **self-improve**. This
repository is developed research-first: see `PROJECT_MEMORY.md` (single source of truth)
and `docs/` (the Phase-0 research foundation) before the code.

> **Scope now:** India cash equities · swing 2–10d upside · **free data** · research +
> paper trading first. Live execution and intraday are designed-for but deferred.

## What's here

```
PROJECT_MEMORY.md      Single source of truth: decisions, risks, roadmap
docs/                  Research foundation (problem def, labeling, data, models, arch)
src/aiscout/           The system
  config.py            All tunables (labels, universe, costs, validation)
  data/synthetic.py    Realistic market simulator (offline demo)
  data/yahoo.py        Live NSE/BSE adapter (real data)
  features.py          Point-in-time feature engine (docs/02)
  labeling.py          Triple-barrier labels + India tradability gate (docs/00)
  validation.py        Purged + embargoed walk-forward CV (docs/03)
  model.py             Rule/logistic baselines + calibrated LightGBM
  metrics.py           PR-AUC, precision@K, Brier, reliability
  backtest.py          Cost-aware portfolio backtest (India cost model)
  alerts.py            Explainable alert schema (docs/04)
  pipeline.py          End-to-end orchestration (the nightly loop)
  report.py            Self-contained HTML dashboard generator
scripts/run_demo.py    Full pipeline on SYNTHETIC data (works offline)
scripts/run_live.py    Full pipeline on REAL NSE data via Yahoo
```

## Quickstart

```bash
pip install -r requirements.txt

# Offline demo on the synthetic market (no network needed):
python scripts/run_demo.py
python -m aiscout.report                       # builds outputs/dashboard.html

# Real data (needs access to Yahoo Finance):
python scripts/run_live.py RELIANCE.NS TCS.NS INFY.NS ...
```

## Honesty contract

- The bundled demo runs on a **synthetic market simulator** because the development
  sandbox blocks live market feeds. Its metrics prove the **pipeline works and can learn
  signal that exists by construction** — they are **not** evidence of a live-market edge.
- On real data, results are unknown until measured. Every metric is out-of-sample and
  **net of the India cost model** (STT, stamp, exchange/SEBI/GST, slippage, impact).
- Nothing here is investment advice.

## Design guarantees (why results aren't self-deception)

- **No look-ahead:** features use only data through close of day *t*; entry is next-day.
- **Purged + embargoed walk-forward:** overlapping triple-barrier labels can't leak.
- **Tradability is part of the label:** locked-circuit / T2T / ASM / F&O-ban setups are
  excluded — an unenterable prediction never counts as a win.
- **Simple-before-complex:** the GBM must beat rule + logistic baselines out-of-sample.
- **Calibration is mandatory:** a "70%" signal should be right ~70% of the time.

See `PROJECT_MEMORY.md §7` for the phased roadmap (P0 research → … → P7 production).
