# 11 · Position Sizing & Risk of Ruin (Indian Stocks)

> The original source had a duplicate "Drawdown Analysis" card here. This library
> repurposes slot #11 into a dedicated **position sizing** prompt, which pairs
> naturally with #09 (Monte Carlo) and #10 (Drawdown).

Choose a position‑sizing scheme that survives a losing streak and respects
Indian‑market frictions.

---

## Prompt

```
Design a position-sizing framework for this strategy on Indian equities:

[PASTE STRATEGY + its stats: win rate, avg win, avg loss (R), trades/year,
cost per trade. If missing, ask me.]

Capital: [₹10,00,000]     Max acceptable drawdown: [e.g. 20%]
Instruments: [cash-intraday MIS / delivery / F&O]

Compare and recommend among:
- Fixed-fractional risk (e.g. risk 1% of equity per trade).
- Volatility-targeting / ATR-based sizing (size inversely to recent volatility
  or India VIX).
- Fractional-Kelly (e.g. quarter- or half-Kelly) with a clear warning about
  full-Kelly's ruin risk.
- Fixed lot / fixed capital-per-trade for F&O (respecting NSE lot sizes and
  SPAN+exposure margin).

For the recommended scheme, give:
- The exact sizing formula and a worked example for ₹10,00,000 capital.
- How many units/shares or F&O lots that implies for a sample trade (round to
  whole lots; check margin is available).
- Portfolio HEAT cap: max total risk across simultaneous open positions, and a
  correlation adjustment (don't take 5 correlated financials at full size).
- A rule to CUT size after a losing streak and restore it after recovery.
- Estimated risk of ruin and probability of breaching the max-drawdown limit.

Indian frictions to bake in:
- STT + brokerage + slippage reduce net edge — show sizing on NET expectancy.
- Circuit limits/gaps can breach stops: add a buffer or cap single-name exposure.
- F&O margin and physical-settlement risk near expiry.
```

---

### Tips
- Pair the output with **#09 Monte Carlo** — validate the chosen size gives an
  acceptable risk of ruin before trading it.
- For F&O, remember one lot can be a large notional; fixed‑fractional often
  rounds to **zero or one lot** on ₹10L — the model should flag when the account
  is too small for the instrument.
