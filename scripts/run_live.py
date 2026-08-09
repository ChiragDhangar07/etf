"""Run AIScout on REAL NSE data via Yahoo Finance.

    python scripts/run_live.py                # Nifty starter universe, 3y
    python scripts/run_live.py RELIANCE.NS TCS.NS INFY.NS

Requires outbound access to query1.finance.yahoo.com (blocked in the research sandbox,
works on your machine). Emits outputs/results_live.json for the dashboard.

For the full India edge (delivery%, ASM/GSM, F&O ban), extend aiscout/data/bhavcopy.py
to merge NSE bhavcopy delivery data into the panel before calling run().
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiscout.config import DEFAULT
from aiscout.data import yahoo
from aiscout.pipeline import run


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_email = "--email" in sys.argv
    symbols = args or yahoo.NIFTY_STARTER
    print(f"Fetching {len(symbols)} symbols from Yahoo Finance ...")
    panel, index_df = yahoo.load(symbols, range_="3y", interval="1d")
    print(f"  got {panel['symbol'].nunique()} symbols x {panel['date'].nunique()} days")

    results = run(panel, index_df, DEFAULT, data_label="LIVE-YAHOO-NSE")
    out = Path(__file__).resolve().parents[1] / "outputs" / "results_live.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Wrote {out}")
    prod = results["production_model"]
    m = results["metrics_oos"][prod]
    print(f"[{prod}] OOS precision@10% {m['precision_at_k']:.1%} "
          f"(lift {m['lift_at_k']:.2f}x) | PR-AUC {m['pr_auc']:.3f}")
    print(f"Today's alerts: {len(results['alerts'])}")

    if do_email:
        from aiscout.notify import email_alerts
        try:
            email_alerts(results)
            print("Email sent.")
        except Exception as e:  # noqa: BLE001
            print(f"Email NOT sent: {e}")


if __name__ == "__main__":
    main()
