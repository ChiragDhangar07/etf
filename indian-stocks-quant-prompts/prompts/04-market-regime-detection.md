# 04 · Market Regime Detection (Indian Stocks)

Classify the current regime of an Indian asset and recommend what to trade — and
what to avoid.

---

## Prompt

```
Analyse current market conditions for [ASSET: e.g. Nifty 50 / Bank Nifty /
RELIANCE / a sector index like Nifty IT].

Use the data I provide (or ask me for it): recent OHLCV, India VIX, advance/
decline, delivery %, and FII/DII flow if available.

Identify:
- Trend: bullish, bearish, or sideways (justify using price structure +
  moving-average configuration, e.g. 20/50/200 DMA on the daily).
- Volatility level: use India VIX and ATR — is it low, normal, or elevated
  vs its own recent range? (Include current India VIX if I gave it to you.)
- Volume/participation behaviour: rising or falling volumes, delivery %
  trend, and FII vs DII net positioning.
- Breadth: % of index constituents above their 50/200 DMA, adv/decline.

Then recommend:
- The best STRATEGY TYPE for this environment (trend-following, mean-reversion,
  breakout, options premium-selling, or stay-flat) with reasoning tied to the
  Indian context (e.g. expiry week behaviour, FII flow direction, event calendar).
- What to AVOID right now (e.g. avoid breakout buying in a low-VIX chop, avoid
  naked option selling into an event, avoid illiquid mid-caps in a risk-off tape).

Finish with a one-line regime label, e.g. "Low-vol uptrend — favour pullback
buys, avoid chasing breakouts."
```

---

### Tips
- Feed it **India VIX** explicitly — it's the single most useful regime input for
  Indian markets and the model can't fetch it live.
- Ask it to output a small **regime → strategy** lookup table you can reuse.
