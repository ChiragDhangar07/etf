# 08 · Trade Setup Generation (Indian Stocks)

Generate concrete, high‑probability trade setups with full risk parameters.

---

## Prompt

```
Based on the data I provide, generate 3 high-probability trade setups for
[MARKET: e.g. Nifty 50 stocks / Bank Nifty / Nifty options].

I will paste: recent price action / levels / chart description / option chain /
India VIX / any news catalyst. Use ONLY this data — if something is missing,
ask me rather than inventing prices.

For EACH trade, include:
- Instrument and side (long / short; cash-intraday or F&O — note that cash
  shorting is intraday-only in India).
- Entry price (and trigger condition, e.g. "buy above ₹X on 15m close").
- Stop-loss (price and ₹ risk per unit/lot).
- Take-profit target(s) (price and R multiple).
- Risk-reward ratio (must be ≥ [1.5]:1 after costs).
- Position size for [₹10,00,000] capital at [1–2%] risk per trade
  (respect F&O lot sizes; round to whole lots).
- Reasoning: technical (structure, levels, indicators) AND macro/flow
  (FII/DII, sector trend, global cues, event calendar).

Rules:
- Deduct realistic Indian costs and slippage when computing R:R.
- Flag any setup that sits into an event (RBI/Budget/results/expiry) as
  higher-risk.
- Avoid illiquid names; note impact cost if the stock is thin.
- Give an invalidation condition for each (what would make you skip/exit).
```

---

### Tips
- Paste an **option chain** for premium‑selling setups and ask for setups with
  defined risk (spreads), not naked shorts.
- Ask for a **checklist** version you can run each morning before the 09:15 open.
