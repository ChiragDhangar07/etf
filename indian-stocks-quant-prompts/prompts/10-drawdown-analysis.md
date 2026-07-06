# 10 · Drawdown Analysis (Indian Stocks)

Characterise a strategy's drawdowns and how to shorten/soften them.

---

## Prompt

```
Analyse the drawdowns of this strategy for Indian equity trading:

[PASTE STRATEGY + equity curve or trade list if available; otherwise ask me
for it or give me code to compute it.]

Provide:
- Max drawdown (₹ and %) and the dates/period it occurred.
- Average and worst drawdown DEPTH.
- Average recovery time (bars/days from trough back to a new high) and the
  longest underwater period.
- Drawdown frequency and whether losses CLUSTER (e.g. during high-VIX regimes,
  expiry weeks, event days, or specific sectors).
- The market conditions present during the worst drawdown (India VIX level,
  trend, FII/DII flows, any macro/global shock).

Then suggest:
- 3 concrete ways to REDUCE drawdowns (e.g. India VIX / ATR volatility gate,
  regime filter to sit out chop, event-day flat rule, correlation cap across
  positions, options hedge on the index).
- Position-sizing improvements (volatility-targeting, reducing size after a
  losing streak, capping total portfolio heat).

Quantify the expected improvement of each suggestion where you can, and note the
trade-off (usually lower drawdown costs some upside — say how much).
```

---

### Tips
- Ask for an **underwater (drawdown) plot** and a table of the top‑5 worst
  drawdowns with their recovery times.
- Cross‑reference the worst periods with the Indian event calendar (Budget,
  major RBI moves, COVID crash, global risk‑off) to see if a simple event filter
  would have helped.
