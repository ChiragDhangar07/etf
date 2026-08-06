# 01 — Data Sources (India, Free Tier)

> Data access is the #1 project risk (R2) and the make-or-break assumption (A4). This
> doc maps what genuinely exists for free, how reliable and legal each source is, and
> what predictive value it unlocks. Reliability/latency claims marked **[fact]** are
> stable; **[hypothesis]** needs Phase-1 verification.

---

## 1. The honest headline

On free tiers, this is an **end-of-day (EOD) system**. Reliable, free, intraday
tick/microstructure data for the whole NSE universe does **not** exist. What *does*
exist for free is a genuinely rich **EOD + daily-flow** dataset that most retail and
even some pro systems underuse. Our edge lives there.

---

## 2. Core EOD price/volume

### 2.1 NSE Bhavcopy (daily) — **the backbone** `[fact]`
- Daily EOD file per exchange: OHLC, close, volume, VWAP, number of trades, plus a
  **separate delivery file** with **deliverable quantity** and **delivery %**.
- Historical archives are downloadable by date. This is our primary EOD source of
  truth for OHLCV **and** the delivery signal.
- **Value unlocked:** clean OHLCV history + **delivery %** (a real accumulation/
  distribution proxy — high delivery on an up-move = conviction, not just churn).
- **Caveats:** format has changed over the years (old vs new UDiFF format); needs
  corporate-action adjustment separately; historical delivery data has a start date.

### 2.2 Yahoo Finance (`.NS` / `.BO`) `[fact]`
- Free adjusted daily OHLCV; limited intraday with short history; easy programmatic
  access (already used by the prior tracker via a CORS proxy).
- **Value:** convenient **split/dividend-adjusted** daily series and index data.
- **Caveats:** no delivery data; occasional bad ticks/gaps for thin Indian names;
  unofficial API, rate-limited, can break without notice.

### 2.3 Free broker APIs (Upstox / Fyers / Angel / Kite) `[hypothesis]`
- With a (free) trading account, several brokers expose **historical candles** and
  **live quotes** via API. Upstox/Fyers historical candle access is commonly free;
  Kite historical is a paid add-on.
- **Value:** the most **robust** ingestion backbone (proper auth, documented, less
  fragile than scraping NSE), plus a future path to **intraday** and **live** data —
  the bridge from "nightly loop" toward "continuously thinking."
- **Caveats:** requires an account + token refresh; rate limits; per-broker quirks.
- **Leaning:** use bhavcopy archives for deep EOD history + a broker API for
  robustness and the eventual intraday upgrade. To validate in Phase 1 (U1).

---

## 3. India-specific flow & positioning data (the underused edge)

| Source | What it gives | Predictive hypothesis | Notes |
|--------|---------------|----------------------|-------|
| **Delivery % (bhavcopy)** `[fact]` | Deliverable qty / traded qty per stock/day | Rising delivery% + price/volume up ⇒ genuine accumulation, precursor to continuation | Core feature; free & daily |
| **FII/DII daily flows** `[fact]` | Provisional net cash buy/sell by FIIs & DIIs | Risk-on/off regime + breadth of institutional demand | Market-level (and sector via other reports) |
| **Bulk & block deals** `[fact]` | Large trades w/ client name, qty, price, daily | Informed/institutional entry footprint in a specific name | Free daily disclosure |
| **F&O Open Interest / PCR / OI buildup** `[fact]` | OI, change in OI, put-call ratio, long/short buildup | OI + price direction ⇒ long buildup vs short covering; squeeze setups | F&O names only |
| **Securities in F&O ban** `[fact]` | Names where OI > 95% market-wide limit | Tradability gate + crowding/squeeze signal | Daily list |
| **ASM / GSM lists** `[fact]` | Surveillance-stage stocks | Tradability gate; also flags manipulation/volatility risk | Daily/periodic |
| **Index constituents & weights** `[fact]` | Nifty50/Next50/500/sector indices membership | Sector rotation, relative strength, breadth | For point-in-time universe |
| **India VIX** `[fact]` | Implied volatility of Nifty | Regime (risk-on/off, vol expansion/contraction) | Market-level feature |

---

## 4. Corporate actions, fundamentals, events

| Source | What | Notes |
|--------|------|-------|
| **NSE/BSE corporate announcements** `[fact]` | Earnings dates, board meetings, dividends, splits, bonus, buybacks, orders/contracts | Event windows are strong move catalysts; needs parsing; timing/latency varies |
| **Corporate actions (splits/bonus/div/rights)** `[fact]` | For price adjustment + event features | Essential for correct returns (R1) |
| **SAST / promoter pledge / insider (SEBI) disclosures** `[fact]` | Promoter buy/sell, pledge changes, acquisitions | Promoter accumulation / de-pledging = bullish tell; free but messy to parse |
| **Fundamentals (Screener.in / Tickertape / Trendlyne)** `[hypothesis]` | Quarterly financials, ratios | Mostly scraped; **ToS/legality caution**; use official filings where possible |
| **Earnings surprise / results calendar** `[fact]` | Result dates & outcomes | Post-earnings drift is a documented swing catalyst |

---

## 5. Macro & cross-asset (free)

- **Global cues:** SGX/GIFT Nifty (pre-market proxy), US indices, Dow/Nasdaq, crude
  (Brent), USDINR, US 10Y yield — all free EOD. Drive gap/risk-on regime.
- **Sector indices** (Nifty Bank, IT, Auto, Pharma, Metal, FMCG, etc.) for rotation
  and relative-strength features.

---

## 6. Reliability, legality, and hygiene rules

- **Respect ToS & rate limits.** NSE endpoints are anti-bot: realistic headers,
  session cookies, polite delays, local caching, and off-hours batch pulls. No
  hammering. Prefer **official archive files** and **broker APIs** over scraping HTML.
- **Fundamentals scraping** (Screener/Tickertape/Trendlyne) is **legally gray** — treat
  as optional/enrichment, prefer official exchange/SEBI filings, and never redistribute.
- **Cache everything locally** and build **point-in-time** stores (so we can reconstruct
  exactly what was known on any past date — critical for leak-free backtests, R1).
- **Redundancy:** at least two independent sources for prices (bhavcopy + Yahoo/broker)
  so one outage doesn't halt research.
- **Data-quality gates:** detect bad ticks, zero-volume days, unadjusted jumps, missing
  delivery files; quarantine and log rather than silently ingest.

---

## 7. What we do NOT have on free tier (state it plainly)

- True order-book / tick-by-tick microstructure (bid/ask depth, order imbalance) for
  the full universe — **not free**. Some of it is inferable at coarse resolution from
  delivery%, OI, and daily VWAP, but not the real thing.
- Real-time dealer/gamma positioning — **not available** in India even paid, in the US
  sense. We approximate crowding via OI/ban-list/PCR only.
- Clean, licensed, survivorship-bias-free fundamental history — **not free**; we
  approximate and flag the limitation.

> This section exists so we never build a feature we can't actually feed. Every feature
> in doc 02 is tagged with the tier it needs.

---

## 8. Feeds this into the memory

- U1 (ingestion backbone) is resolved by a Phase-1 spike: attempt bhavcopy archive
  ingestion + one broker API, measure reliability, pick the backbone, record in memory.
- A4 (can we actually get clean adjusted OHLCV + delivery for a liquid universe) is
  **proven or disproven** in Phase 1 before any modeling.
