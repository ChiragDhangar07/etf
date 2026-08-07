"""Run the full AIScout pipeline on the SYNTHETIC market and emit results.

    python scripts/run_demo.py

Outputs outputs/results.json (consumed by the dashboard). SYNTHETIC data is used
because the sandbox blocks live market hosts; metrics here validate the pipeline, not
a live edge. To run on real data see scripts/run_live.py.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiscout.config import DEFAULT
from aiscout.data.synthetic import simulate
from aiscout.pipeline import run


def main():
    t0 = time.time()
    print("[1/3] Simulating synthetic market ...")
    panel, index_df = simulate(n_symbols=140, n_days=1400, seed=7)
    print(f"      {panel['symbol'].nunique()} symbols x {panel['date'].nunique()} days")

    print("[2/3] Running pipeline (features -> labels -> walk-forward -> backtest -> alerts) ...")
    results = run(panel, index_df, DEFAULT, data_label="SYNTHETIC")

    out = Path(__file__).resolve().parents[1] / "outputs" / "results.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"[3/3] Wrote {out}  ({time.time()-t0:.1f}s)")

    m = results["metrics_oos"]["gbm"]
    b = results["backtest"]
    print("\n--- OOS (walk-forward) GBM ---")
    print(f"  base rate       : {m['base_rate']:.3%}")
    print(f"  precision@10%   : {m['precision_at_k']:.3%}  (lift {m['lift_at_k']:.2f}x)")
    print(f"  PR-AUC          : {m['pr_auc']:.3f}   ROC-AUC {m['roc_auc']:.3f}")
    print(f"  Brier           : {m['brier']:.4f}")
    if "error" not in b:
        print("--- Cost-aware backtest (SYNTHETIC) ---")
        print(f"  trades {b['n_trades']} | hit {b['hit_rate']:.1%} | "
              f"CAGR {b['cagr']:.1%} | Sharpe {b['sharpe']:.2f} | "
              f"maxDD {b['max_drawdown']:.1%} | PF {b['profit_factor']:.2f}")
    print(f"  alerts generated: {len(results['alerts'])}")


if __name__ == "__main__":
    main()
