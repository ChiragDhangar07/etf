# 09 · Monte Carlo Simulation (Indian Stocks)

Stress‑test a strategy by simulating many possible futures from its trade
distribution.

---

## Prompt

```
Run a Monte Carlo analysis on this strategy for Indian equities:

[PASTE STRATEGY + its trade statistics: win rate, avg win (R or ₹), avg loss,
number of trades per year, and cost per trade. If I don't have these, ask.]

Capital: [₹10,00,000]     Risk per trade: [1–2%]

Method:
- Simulate [10,000] equity paths by resampling / bootstrapping the trade
  outcomes (with replacement) over a [1-year / 250-trade] horizon.
- Include realistic Indian costs per trade in every simulated outcome.
- Optionally model fat tails / gap risk (a small probability of an outsized
  adverse move from overnight global cues or a circuit-lock that blows the stop).

Show:
- Probability of loss (ending below starting capital) and probability of
  hitting a [-20%] drawdown.
- Return distribution: median, 5th and 95th percentile ending equity (₹ and %).
- Worst-case scenarios: the 1st-percentile path and its max drawdown.
- Risk of ruin at the chosen position size.

Then judge:
- Is this strategy ROBUST or FRAGILE? Justify using the spread of outcomes and
  the tail behaviour, not just the average.
- What position size keeps risk-of-ruin acceptably low?

If you can't run it here, give me runnable Python (numpy) that performs the
bootstrap and prints/plots the distribution, and label any inline figures as
illustrative.
```

---

### Tips
- The Indian twist worth adding: a small **gap/circuit tail** — stops don't
  always fill at your price on a lower circuit. Ask the model to include a
  "stop slippage" term.
- Use the output to pick position size, not to admire the median return.
