# 00 · Reusable Indian‑Market Context Block

Prepend this block to **any** of the prompts in this library (or your own) to lock
the model into the correct Indian‑market assumptions. Copy it, fill the blanks,
paste it above your actual instruction.

---

```
CONTEXT — INDIAN EQUITY MARKETS
- Exchanges: NSE and BSE. Reference NSE symbols (e.g. RELIANCE, HDFCBANK, INFY)
  and indices: Nifty 50, Nifty Bank, Nifty Midcap 150, Nifty Smallcap 250,
  Nifty 500, Sensex, and relevant NSE sectoral indices.
- Currency: all capital, prices, P&L and costs in ₹ (INR). Use lakh/crore where
  natural (1 lakh = 1,00,000; 1 crore = 1,00,00,000).
- Trading session: 09:15–15:30 IST (pre-open 09:00–09:15). Settlement T+1.
  Daily circuit limits / price bands apply per scrip.
- Transaction costs to model on every trade: brokerage, STT (Securities
  Transaction Tax), exchange transaction charges, GST, SEBI turnover fee,
  stamp duty, and impact cost/slippage (higher for mid/small caps).
- F&O (if used): NSE lot sizes, weekly index expiry / monthly stock expiry,
  SPAN + exposure margin, physical settlement for stock F&O on expiry.
- Macro drivers relevant to India: RBI repo rate & policy stance, CPI/WPI
  inflation, GDP growth, monsoon, crude oil (India is a net importer),
  USD/INR, fiscal deficit, and FII/DII net flows.
- Regulator: SEBI. Note taxation context where relevant (intraday = speculative
  business income; delivery = STCG/LTCG), but do NOT give tax advice.
- Data realism: account for liquidity — many mid/small caps have wide spreads
  and low volume; avoid assuming fills that impact cost would erase.

OUTPUT RULES
- State all assumptions explicitly.
- Flag any number you are estimating vs. computing from provided data.
- Never present hypothetical backtest figures as if they were real results.
```

---

Then add your specific instruction below the block, e.g.:

```
TASK: <paste one of the prompts 01–13 here, with placeholders filled in>
```
