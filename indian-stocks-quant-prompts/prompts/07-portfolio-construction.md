# 07 · Portfolio Construction (Indian Stocks)

Build a diversified ₹ portfolio across Indian assets for a given risk tolerance
and horizon.

---

## Prompt

```
Build a diversified portfolio (in ₹) from these assets:

[LIST: e.g. NIFTYBEES (Nifty 50 ETF), a few large-cap stocks like RELIANCE /
HDFCBANK / INFY, a gold ETF like GOLDBEES, a debt/G-sec option like a liquid
bond ETF or a target-maturity fund, and optionally a Nasdaq/US ETF like
MON100 for global diversification]

Constraints:
- Total capital: [₹10,00,000]
- Risk tolerance: [low / medium / high]
- Time horizon: [e.g. 1 to 3 years]
- Long-only, delivery/holdings (no leverage).

Output a table with, per asset:
- Allocation percentage and ₹ amount.
- Expected annual return (state your assumption/source and label as an estimate).
- Risk: expected volatility and worst-case drawdown.
- Role in the portfolio and WHY it's included (growth / stability / inflation
  hedge / global diversification / income).

Portfolio-level output:
- Blended expected return, volatility, and estimated max drawdown.
- Correlation notes (e.g. equity vs gold vs debt behaviour in Indian risk-off
  episodes; INR depreciation helping global/gold sleeves).
- Diversification check: sector concentration (Indian indices are
  financials-heavy — flag if the book is over-exposed).
- Rebalancing rule (e.g. annual or ±5% band) and a note on tax/exit-load and
  STT/LTCG friction from rebalancing.

Keep it realistic for an Indian retail investor: mention ETF liquidity, expense
ratios, and that debt/gold ETFs on NSE can have tracking error and low volume.
```

---

### Tips
- For a purely passive version, ask for an **index‑ETF‑only** portfolio
  (NIFTYBEES / JUNIORBEES / GOLDBEES / a G‑sec ETF) to minimise cost and effort.
- Ask it to show the same portfolio at **low vs high** risk so you can compare.
