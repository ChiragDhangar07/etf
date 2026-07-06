# 05 · Multi‑Factor Strategy (Indian Stocks)

Build a factor model (momentum + value + volatility + trend) over an Indian
stock universe.

---

## Prompt

```
Create a multi-factor equity strategy over an Indian stock universe.

Universe: [e.g. Nifty 50 / Nifty 200 / Nifty 500 — state it]
Capital: [₹10,00,000]     Rebalance capital constraint: long-only, cash/delivery.

Factors to combine:
- Momentum  — [e.g. 12-1 month total return, skipping the most recent month]
- Value     — [e.g. earnings yield (E/P), P/B, EV/EBITDA — India-relevant]
- Volatility— [e.g. inverse of 6-month realised vol / low-beta]
- Trend     — [e.g. price above 200-DMA, positive 50-DMA slope]

For each factor, include:
- Exact formula / logic and the data field it needs (and where to get it for
  Indian stocks — e.g. NSE, screener data, yfinance fundamentals).
- How you rank/normalise it cross-sectionally (z-score or percentile rank).

Then define the combined model:
- Weight allocation % per factor (state the weights, e.g. 35/25/20/20) and why.
- Portfolio construction: number of holdings (e.g. top 20), weighting (equal /
  score-weighted / vol-weighted), and single-stock cap.
- Rebalancing frequency (e.g. monthly) and turnover expectation — then subtract
  realistic Indian round-trip costs (brokerage + STT + charges + slippage).
- Liquidity screen: minimum median daily traded value (₹) so you avoid names you
  can't actually trade.

Deliver:
- The scoring methodology as clear pseudocode.
- An EXAMPLE portfolio (a plausible current top-20 with weights) — clearly
  labelled illustrative if not computed from real data.
- Expected behaviour by regime (which factor leads in risk-on vs risk-off India).
```

---

### Tips
- Indian value data is patchy in free sources — ask for a version that uses only
  fields available from `yfinance` / NSE + a fallback if a field is missing.
- Add a **sector cap** so the book isn't 60% financials (Bank/Financials dominate
  Indian indices).
