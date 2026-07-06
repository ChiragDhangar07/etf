# 03 · Risk‑Reward Analysis (Indian Stocks)

Break down a strategy's risk/reward profile and propose concrete improvements.

---

## Prompt

```
Analyse this strategy's risk-reward profile for Indian equity trading:

[PASTE STRATEGY]

Capital: [₹10,00,000]     Risk per trade: [1–2%]     Instrument: [cash / F&O]

Break down:
- Risk per trade (in ₹ and % of capital) after costs.
- Reward-to-risk ratio (average and distribution, not just the target R:R).
- Drawdown patterns (typical depth, duration, and clustering of losses).
- Expectancy per trade in ₹ (win% × avg win − loss% × avg loss − costs).
- Sensitivity to Indian-specific risks:
    * Gap risk from overnight global cues (SGX/GIFT Nifty, US close, crude).
    * Event risk: RBI policy, Union Budget, quarterly results, expiry days.
    * Liquidity/impact cost, especially for mid & small caps.
    * Circuit-limit lock-ups (can't exit at your stop).

Then:
- Suggest 3 improvements to REDUCE risk (e.g. volatility-scaled position sizing,
  event-day filters, hedging with Nifty/stock options, tighter liquidity screen).
- Suggest 2 ways to INCREASE returns WITHOUT increasing risk (e.g. better entry
  timing, regime filter to avoid choppy phases, cost reduction via fewer/larger
  trades, holding winners with a trailing ATR stop).

Quantify the expected effect of each suggestion where possible, and state your
assumptions.
```

---

### Tips
- Follow up with: *"Re‑run the expectancy math assuming round‑trip cost of X bps
  and a Y% worse fill on stops due to slippage."*
