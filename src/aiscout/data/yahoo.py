"""Live Yahoo Finance adapter for NSE/BSE (real data).

Returns the SAME canonical panel schema as the synthetic simulator, so the entire
downstream pipeline is source-agnostic. Yahoo provides split/dividend-adjusted daily
OHLCV but NOT delivery% or India surveillance flags -- those columns are left NaN/0 and
the model degrades gracefully (LightGBM handles NaN natively). For the full India edge
(delivery%, ASM/GSM, F&O ban) pair this with the bhavcopy adapter.

NOTE: This module makes outbound HTTPS calls and therefore only works where the network
policy permits query1.finance.yahoo.com. In the research sandbox those hosts are blocked
(HTTP 403), which is why the demo uses synthetic data.
"""
from __future__ import annotations

import time
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _fetch_one(symbol: str, range_: str, interval: str) -> pd.DataFrame | None:
    url = f"{_CHART}{urllib.parse.quote(symbol)}?range={range_}&interval={interval}"
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            import json
            data = json.load(r)
    except Exception as e:  # noqa: BLE001
        print(f"  ! {symbol}: {e}")
        return None
    res = data.get("chart", {}).get("result")
    if not res:
        return None
    res = res[0]
    ts = res.get("timestamp")
    q = res.get("indicators", {}).get("quote", [{}])[0]
    adj = res.get("indicators", {}).get("adjclose", [{}])
    if not ts:
        return None
    df = pd.DataFrame({
        "date": pd.to_datetime(ts, unit="s").normalize(),
        "open": q.get("open"), "high": q.get("high"),
        "low": q.get("low"), "close": q.get("close"),
        "volume": q.get("volume"),
    })
    if adj and adj[0].get("adjclose"):
        # scale OHLC by the adjustment ratio to keep splits/dividends consistent
        ratio = np.array(adj[0]["adjclose"], dtype=float) / df["close"].to_numpy()
        for c in ("open", "high", "low", "close"):
            df[c] = df[c] * ratio
    df["symbol"] = symbol
    # columns the India pipeline expects but Yahoo lacks -> neutral defaults
    df["delivery_pct"] = np.nan
    for c in ("upper_circuit", "lower_circuit", "t2t", "asm", "fno_ban"):
        df[c] = 0
    return df.dropna(subset=["close"]).reset_index(drop=True)


def load(symbols: list[str], range_: str = "3y", interval: str = "1d",
         index_symbol: str = "^NSEI", pause: float = 0.4):
    """Fetch a universe + index. Returns (panel, index_df) in canonical schema."""
    frames = []
    for sym in symbols:
        df = _fetch_one(sym, range_, interval)
        if df is not None and len(df) > 60:
            frames.append(df)
        time.sleep(pause)  # be polite to the endpoint
    if not frames:
        raise RuntimeError("No data fetched (network policy may block Yahoo).")
    panel = pd.concat(frames, ignore_index=True)
    idx = _fetch_one(index_symbol, range_, interval)
    index_df = (idx[["date", "close"]] if idx is not None
                else panel.groupby("date")["close"].mean().reset_index())
    return panel, index_df


# A liquid starter universe (NSE). Extend freely.
NIFTY_STARTER = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "WIPRO.NS", "ADANIENT.NS",
]
