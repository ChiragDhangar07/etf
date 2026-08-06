# 02 — Feature Catalog

> Candidate predictive variables for the swing (2–10 day) upside-explosion target on
> free Indian EOD data. Each feature is tagged with the **data tier** it needs and a
> one-line **hypothesis**. None is assumed useful — every one must earn its place via
> feature-importance + ablation on out-of-sample data (doc 03). This is a menu to test,
> not a model.

**Tier legend:** `EOD` = free bhavcopy/Yahoo · `FLOW` = free India flow/OI/delivery ·
`EVENT` = announcements/corp-actions · `MACRO` = free cross-asset · `FUND?` =
fundamentals (gray/optional).

---

## 1. Price action & momentum (`EOD`)
- **Returns** over 1/3/5/10/20/60d — trend & momentum. *H: persistence precedes
  continuation.*
- **Distance from N-day high/low** (52w, 20d) — proximity to breakout. *H: coiling near
  highs precedes expansion.*
- **Breakout flags** — close above 20/50-day high; N-day range breakout. *H: range
  expansion after contraction is explosive.*
- **Gap features** — overnight gap %, gap vs ATR. *H: gaps signal information shocks.*
- **Consecutive up/down days, streak length.** *H: accumulation streaks.*
- **Position in daily range** (close vs high-low) over recent days. *H: strong closes =
  demand.*

## 2. Volatility structure (`EOD`)
- **ATR% (20d)** and its trend — the scaling backbone for labels & features.
- **Volatility contraction (NR7 / inside-day / Bollinger squeeze)** — *H: vol
  contraction precedes vol expansion (the coil).* One of the strongest swing priors.
- **Realized vol ratios** (5d/20d, 20d/60d) — expansion vs contraction regime.
- **High-low range compression** percentile. *H: tight range = stored energy.*

## 3. Volume & participation (`EOD` + `FLOW`)
- **Relative volume (RVOL)** = today's volume / avg(N) — *H: abnormal volume marks the
  start of a move.* Core.
- **Volume trend / OBV / accumulation-distribution.** *H: rising OBV = stealth accum.*
- **Delivery %** and **delivery-weighted volume** (`FLOW`) — *H: high delivery on
  up-days = real accumulation, not intraday churn.* India-specific edge.
- **Volume dry-up then spike** pattern. *H: dry-up (contraction) → spike (ignition).*
- **VWAP position** (close vs day VWAP; multi-day). *H: closing above VWAP = demand.*

## 4. Relative strength & cross-sectional (`EOD` + `MACRO`)
- **RS vs Nifty / vs sector index** (ratio & its slope) over 5/20/60d. *H: leaders lead.*
- **Cross-sectional return rank / percentile** within universe & within sector. *H: top
  decile momentum continues short-term.*
- **Sector momentum & sector rotation rank.** *H: money rotates into hot sectors.*
- **Beta / correlation to Nifty** (regime-dependent usefulness).

## 5. Market breadth & regime (`MACRO` + `FLOW`)
- **Advance/decline, % above 50/200-DMA, new-highs/new-lows.** *H: broad tape supports
  individual breakouts.*
- **India VIX level & change** — *H: vol regime gates breakout success.*
- **FII/DII net flow (level & trend)** (`FLOW`) — *H: institutional risk-on lifts the
  probability base rate.*
- **Nifty regime label** (trend/range, vol bucket) from a regime model (doc 03/04).

## 6. Options / positioning (`FLOW`, F&O names only)
- **OI + change-in-OI vs price** → long buildup / short covering / short buildup /
  long unwinding. *H: price↑ + OI↑ = fresh longs → continuation.*
- **PCR (put-call ratio)** level & change. *H: extreme PCR = sentiment/squeeze setup.*
- **F&O ban-list membership / proximity** — crowding + squeeze + tradability gate.
- **IV / IV-percentile** (where derivable). *H: IV expansion accompanies moves.*

## 7. Event & catalyst (`EVENT`)
- **Days-to / days-since earnings**; **in earnings window** flag. *H: post-earnings
  drift; pre-earnings positioning.*
- **Corporate action flags** (bonus/split/buyback/dividend/order-win announcements).
  *H: catalysts trigger repricing.*
- **Bulk/block deal in name** (`FLOW`) — *H: informed footprints precede moves.*
- **Promoter pledge change / SAST buy** (`EVENT`) — *H: promoter accumulation/
  de-pledging is bullish.*

## 8. Liquidity & microstructure proxies (`EOD` + `FLOW`)
- **Turnover (₹) & its trend**, Amihud illiquidity proxy (|ret|/turnover). *H:
  improving liquidity accompanies institutional entry; also a tradability gate.*
- **Spread proxy / impact proxy** from daily range & turnover (coarse). *H: tightening
  = healthier participation.*
- **Circuit-band context** (how close to circuit; recent circuit hits). *H: repeated
  upper-circuit near breakout = momentum but tradability risk.*

## 9. Macro / cross-asset (`MACRO`)
- **USDINR, Brent crude, US 10Y, Dow/Nasdaq overnight, GIFT/SGX Nifty** — gap & risk
  regime. *H: global risk-on raises the base rate; sector-specific (crude→energy).*

## 10. Behavioral / time-based (`EOD`)
- **Day-of-week, day-of-month, expiry-week, month-turn/quarter-turn** effects. *H: known
  calendar/flow seasonalities.*
- **Time since last explosive move** (self-history). *H: base-rate conditioning.*

## 11. Historical-analog / anomaly features (derived)
- **Anomaly score** (isolation-forest / Mahalanobis on the feature vector) — *H: today
  looks statistically unusual vs the stock's own history → something is happening.*
- **Nearest-historical-analog similarity** and the forward outcome of those analogs —
  feeds the "compare current behavior to historical behavior" mandate and the
  explainable alert ("this resembles N past setups; M exploded").

---

## Cross-cutting notes
- **Cross-sectional normalization:** most features should be **ranked/z-scored per day
  across the universe** (and within sector) so the model learns *relative* standing, not
  absolute levels that drift with the index. This is critical for cross-sectional swing
  models.
- **Point-in-time only:** every feature computed from data known at/before close of day
  *t*. No exceptions (R1).
- **Automated feature discovery** (later phases): systematically test interactions,
  transforms, and new candidates; keep only those that survive OOS ablation.
- **Feature realism:** `FUND?`-tier features are optional and gated on legal/reliable
  access; the system must perform acceptably on `EOD`+`FLOW`+`EVENT`+`MACRO` alone.
