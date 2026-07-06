# 06 · Strategy Optimization (Indian Stocks)

Improve a strategy's Sharpe and drawdown with a disciplined, overfit‑aware
process.

---

## Prompt

```
Optimise this trading strategy for Indian equities:

[PASTE STRATEGY RULES]

Goals (in priority order):
1. Increase Sharpe ratio.
2. Reduce max drawdown.
(Do NOT just maximise CAGR — I care about risk-adjusted, tradable returns.)

Improve, and explain the rationale for each change:
- Indicator settings (avoid curve-fitting: test parameter ranges, prefer robust
  plateaus over single lucky values; show sensitivity).
- Entry and exit timing (e.g. confirm on close, avoid the first/last 15 min of
  the IST session, avoid entries into RBI policy / Budget / results).
- Filters for trend, volume/liquidity, and volatility (India VIX / ATR regime
  gates; minimum ₹ traded-value liquidity filter).
- Cost reduction: fewer, higher-conviction trades to cut STT + brokerage +
  slippage drag (critical for Indian intraday strategies).

Guardrails against overfitting:
- Use walk-forward / out-of-sample split and report in-sample vs out-of-sample.
- Penalise parameter sets that only work in one regime.
- Keep the number of tunable parameters small.

Deliver a clear BEFORE vs AFTER comparison table:
- CAGR, Sharpe, Sortino, max drawdown, win rate, profit factor, # trades,
  turnover, and total cost drag — for the original vs optimised version.
- A short note on WHY the optimised version should generalise, not just fit
  the past.

If you don't have the data, provide runnable Python that performs the
walk-forward optimisation on .NS data and prints the before/after table.
```

---

### Tips
- Push back on the model if it hands you a suspiciously perfect Sharpe — ask for
  the **out‑of‑sample** number and the **parameter sensitivity heatmap**.
