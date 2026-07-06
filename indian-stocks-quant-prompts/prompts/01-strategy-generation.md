# 01 · Strategy Generation (Indian Stocks)

Generate profitable, rules‑based trading strategies for a chosen Indian market
segment.

---

## Prompt

```
Act as a hedge fund quant specialising in Indian equity markets. Generate 3
profitable, fully rules-based trading strategies for:

[SEGMENT: e.g. Nifty 50 stocks / Bank Nifty index / Nifty Midcap 150 /
 a single stock like RELIANCE / Nifty weekly options]

Constraints:
- Timeframe: [e.g. 1D swing / 15m intraday / weekly positional]
- Capital: [₹10,00,000]
- Risk per trade: [1 to 2% of capital]
- Instruments allowed: [cash/delivery only | intraday MIS | F&O]
- Trading session: 09:15–15:30 IST; assume T+1 settlement for delivery.

For EACH strategy, provide:
1. Indicators used with exact settings (period, source, thresholds).
2. Step-by-step entry and exit rules (precise, backtestable, no ambiguity).
3. Stop-loss and take-profit logic (in ₹ and in % / ATR terms).
4. Market conditions where it works best (trend/range, high/low volatility,
   pre/post-expiry, event days like RBI policy / Budget / earnings).
5. Why this strategy has an edge in the INDIAN market specifically
   (e.g. FII/DII flow behaviour, expiry-day dynamics, gap behaviour after
   global cues, sector rotation, retail crowding).

Indian-market realism you MUST respect:
- Model transaction costs: brokerage + STT + exchange charges + GST + stamp
  duty + slippage. State the round-trip cost assumption in bps.
- Respect liquidity: only use liquid names; note impact cost for mid/small caps.
- Respect circuit limits and no-shorting-in-cash rules (shorting only intraday
  or via F&O).
- If using F&O, state lot size, margin, and expiry handling.

Present each strategy in its own clearly labelled section.
```

---

### Tips
- Swap `[SEGMENT]` for something liquid first (Nifty 50 / Bank Nifty) before
  testing on mid/small caps where costs bite harder.
- Ask a follow‑up: *"Now express Strategy 1 as pseudocode / Pine Script /
  Python (using yfinance with .NS symbols)."*
