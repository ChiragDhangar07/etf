# 02 · Backtesting (Indian Stocks)

Backtest a strategy on Indian historical data with the standard performance
metrics.

---

## Prompt

```
Backtest this trading strategy on Indian equity data:

[PASTE STRATEGY RULES]

Universe / instrument: [e.g. Nifty 50 constituents / RELIANCE.NS / Bank Nifty]
Data source assumption: [e.g. NSE bhavcopy / yfinance .NS / Kite historical]

Requirements:
- Time period: last 5 to 10 years (state the exact window used).
- Bar size: [1D / 15m / etc.]
- Metrics to report: CAGR, Sharpe ratio (annualised, ₹ risk-free = current
  ~1yr T-bill / MIBOR proxy — state it), Sortino, max drawdown, win rate,
  average win/loss (₹ and R), profit factor, number of trades, exposure %.
- Costs: deduct realistic round-trip costs — brokerage + STT + exchange txn
  charges + GST + SEBI fee + stamp duty + slippage. State the total in bps and
  apply it to every trade.
- Output: a results TABLE plus a plain-English summary.

Also handle Indian-market specifics:
- Adjust for splits, bonuses and dividends (state whether prices are adjusted).
- Note survivorship bias if using current index constituents.
- Exclude/flag illiquid days and circuit-limit days.
- If F&O: roll contracts correctly at expiry and include roll cost.

Then explain:
- When the strategy performs BEST and WORST (regime, volatility, expiry week,
  event days such as RBI policy, Union Budget, earnings season).
- What market conditions BREAK it (gap risk from global cues, low-liquidity
  regimes, sharp regime shifts, cost drag on high-frequency variants).

IMPORTANT: If you do not have the actual price data, do NOT fabricate numbers.
Instead, give me runnable Python (yfinance/pandas) that computes these metrics,
and clearly label any illustrative figures as hypothetical.
```

---

### Tips
- Always ask for the **code**, not just numbers — LLM‑invented backtest stats
  are the single biggest trap. Run it yourself on real `.NS` data.
- For intraday strategies, get **minute data** from Kite/Upstox; yfinance
  intraday history is limited (~60 days).
