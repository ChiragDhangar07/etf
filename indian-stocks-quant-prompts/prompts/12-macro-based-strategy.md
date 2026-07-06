# 12 · Macro‑Based Strategy (Indian Stocks)

Build a strategy driven by Indian macro indicators and flows.

---

## Prompt

```
Create a trading/allocation strategy for Indian equities driven by macro
indicators.

Macro inputs to use:
- Interest rates: RBI repo rate & policy stance, 10Y G-sec yield, yield curve.
- Inflation: CPI (and WPI), vs the RBI's ~4% (±2%) target.
- Growth: GDP growth, PMI (manufacturing & services), IIP.
- Currency & commodities: USD/INR, Brent crude (India is a net oil importer).
- Flows: FII and DII net equity flows (the dominant Indian flow signal).
- Global: US Fed policy / DXY / US 10Y, since they drive FII risk appetite.

Explain:
- How EACH factor affects Indian equities and which SECTORS it rotates into/out
  of. Examples to reason about (verify, don't just assert):
    * Falling rates / dovish RBI → rate-sensitives (banks, autos, real estate,
      NBFCs) tend to benefit.
    * Rising crude / weak INR → pressure on OMCs, paints, aviation, importers;
      IT & pharma (exporters) can benefit from a weak INR.
    * Strong FII inflows → large-cap, index-heavy leadership; outflows → risk-off.
- Concrete entry and exit SIGNALS from these factors (define thresholds, e.g.
  "go overweight rate-sensitives when RBI shifts to neutral/accommodative and
  10Y yield rolls over").
- Rebalancing frequency (macro is slow — monthly/quarterly) and how to combine
  the macro tilt with a simple trend filter so you're not fighting price.

Provide:
- A sector-rotation MAP (macro state → overweight/underweight sectors/indices,
  e.g. Nifty Bank, Nifty IT, Nifty Auto, Nifty FMCG, Nifty Energy).
- 2–3 EXAMPLE trades/allocations for a plausible current macro backdrop
  (label assumptions; I'll supply live data if you ask).
- Where to get each data point in India (RBI, MoSPI, NSE FII/DII, etc.).
```

---

### Tips
- Give the model the **latest** repo rate, CPI print and FII/DII figures — it
  can't fetch them and will otherwise use stale training‑data values.
- Ask for the output as a **macro dashboard → sector tilt** table you can update
  monthly.
