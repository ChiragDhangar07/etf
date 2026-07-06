# Indian Stocks — Quant Trading Prompt Library

A library of **13 quant/trading prompt templates**, adapted specifically for the
**Indian equity markets** (NSE & BSE). Each prompt is engineered to be pasted
into an LLM (Claude, ChatGPT, etc.) to help you generate, backtest, analyse and
optimise trading strategies with the right Indian‑market context baked in —
Nifty & Sensex, ₹ (INR) capital, SEBI rules, STT/brokerage costs, IST trading
hours, F&O lot sizes, RBI/FII‑DII macro drivers, and more.

> ⚠️ **Disclaimer:** These are research and educational prompt templates. Nothing
> here is investment advice. LLMs can and do produce plausible‑looking but wrong
> numbers — always validate every backtest, statistic and trade idea against
> real data and your own judgement before risking capital. Trading in equities
> and F&O carries risk of loss.

---

## How to use

1. Open the prompt you need from [`prompts/`](./prompts).
2. Copy the whole template.
3. Replace every `[bracketed placeholder]` with your own inputs.
4. Paste into your LLM of choice.
5. Sanity‑check the output — especially any numbers — before acting on it.

For best results, feed the model **real data** (price history, fundamentals,
option chains). See [Data sources](#data-sources-for-indian-markets) below.

---

## The 13 prompts

| # | Prompt | What it does |
|---|--------|--------------|
| 1 | [Strategy Generation](./prompts/01-strategy-generation.md) | Generate 3 profitable strategies for a chosen Indian market/segment |
| 2 | [Backtesting](./prompts/02-backtesting.md) | Backtest a strategy on 5–10 yrs of Indian data with CAGR, Sharpe, DD, win‑rate |
| 3 | [Risk‑Reward Analysis](./prompts/03-risk-reward-analysis.md) | Break down risk/reward and suggest improvements |
| 4 | [Market Regime Detection](./prompts/04-market-regime-detection.md) | Classify current trend/volatility/volume regime for an Indian asset |
| 5 | [Multi‑Factor Strategy](./prompts/05-multi-factor-strategy.md) | Build a momentum/value/volatility/trend factor model for NSE stocks |
| 6 | [Strategy Optimization](./prompts/06-strategy-optimization.md) | Improve Sharpe and reduce drawdown with before/after comparison |
| 7 | [Portfolio Construction](./prompts/07-portfolio-construction.md) | Build a diversified ₹ portfolio across Indian assets |
| 8 | [Trade Setup Generation](./prompts/08-trade-setup-generation.md) | Generate 3 high‑probability trades with entry/SL/target |
| 9 | [Monte Carlo Simulation](./prompts/09-monte-carlo-simulation.md) | Stress‑test a strategy's return distribution and worst case |
| 10 | [Drawdown Analysis](./prompts/10-drawdown-analysis.md) | Max drawdown, recovery time, mitigation |
| 11 | [Position Sizing & Risk of Ruin](./prompts/11-position-sizing.md) | Position‑sizing improvements and risk‑of‑ruin (dedup of the two "Drawdown" cards) |
| 12 | [Macro‑Based Strategy](./prompts/12-macro-based-strategy.md) | Trade on RBI rates, CPI, growth, USD/INR, crude, FII/DII flows |
| 13 | [Alpha & Edge Detection](./prompts/13-alpha-edge-detection.md) | Find under‑exploited, behaviourally‑driven edges in Indian markets |

> **Note on #10/#11:** The original source had two identical "Drawdown Analysis"
> cards. This library keeps #10 as pure drawdown analysis and repurposes #11 into
> a dedicated **Position Sizing & Risk of Ruin** prompt so nothing is wasted.

---

## What "adapted for Indian stocks" means

Every template has been rewritten so the model reasons in the right context:

- **Instruments & indices:** Nifty 50, Nifty Bank (Bank Nifty), Nifty Midcap 150,
  Nifty Smallcap 250, Nifty 500, Sensex, and NSE sectoral indices — plus single
  stocks by NSE symbol (e.g. `RELIANCE`, `HDFCBANK`, `INFY`).
- **Currency & capital:** All capital and P&L in **₹ (INR)**; example capital of
  **₹10,00,000 (₹10 lakh)** instead of `$10,000`.
- **Costs modelled:** Brokerage, **STT** (Securities Transaction Tax), exchange
  transaction charges, GST, SEBI turnover fees, stamp duty, and **impact cost**
  for illiquid mid/small caps. These matter enormously for high‑frequency and
  intraday strategies.
- **F&O specifics:** NSE lot sizes, weekly index expiries & monthly stock
  expiries, margin (SPAN + exposure), and physical settlement of stock F&O.
- **Session & microstructure:** IST hours **09:15–15:30** (pre‑open 09:00–09:15),
  **T+1** settlement, and daily **circuit limits / price bands**.
- **Macro drivers:** RBI repo rate & policy, CPI/WPI inflation, GDP, monsoon,
  crude oil (India is a net importer), **USD/INR**, fiscal deficit, and
  **FII/DII** flows — the dominant flow signal in Indian equities.
- **Taxation awareness:** Intraday = speculative/business income; STCG vs LTCG on
  delivery; STT‑paid treatment. (Prompts flag tax as a consideration, not advice.)

---

## Data sources for Indian markets

| Source | Use | Notes |
|--------|-----|-------|
| [NSE India](https://www.nseindia.com) | Prices, option chain, bhavcopy, indices | Official; rate‑limited, needs headers |
| [BSE India](https://www.bseindia.com) | Prices, corporate actions | Official |
| Yahoo Finance | OHLCV history | Use `.NS` (NSE) / `.BO` (BSE) suffixes, e.g. `RELIANCE.NS` |
| `yfinance` (Python) | Bulk history | Easiest for backtests |
| `nsepy` / `jugaad-data` | NSE history, F&O | Community libraries |
| Zerodha **Kite Connect** | Live + historical, orders | Paid API |
| Upstox / Angel One **SmartAPI** | Live + historical, orders | Broker APIs |
| RBI DBIE, MoSPI | Macro (rates, CPI, GDP) | Official macro data |

See [`prompts/00-context-block.md`](./prompts/00-context-block.md) for a reusable
"Indian market context" block you can prepend to **any** prompt.

---

## Repo layout

```
indian-stocks-quant-prompts/
├── README.md
└── prompts/
    ├── 00-context-block.md          # reusable Indian-market context
    ├── 01-strategy-generation.md
    ├── 02-backtesting.md
    ├── 03-risk-reward-analysis.md
    ├── 04-market-regime-detection.md
    ├── 05-multi-factor-strategy.md
    ├── 06-strategy-optimization.md
    ├── 07-portfolio-construction.md
    ├── 08-trade-setup-generation.md
    ├── 09-monte-carlo-simulation.md
    ├── 10-drawdown-analysis.md
    ├── 11-position-sizing.md
    ├── 12-macro-based-strategy.md
    └── 13-alpha-edge-detection.md
```

---

## License

MIT — see [`LICENSE`](./LICENSE). Use freely, at your own risk.
