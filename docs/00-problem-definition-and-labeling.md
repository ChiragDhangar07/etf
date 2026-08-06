# 00 — Problem Definition & Labeling

> If we get this document wrong, every model, backtest, and alert built on top is
> wrong. This is the foundation. Everything here is a **proposal to be validated
> empirically in Phase 1**, not a fixed truth.

---

## 1. What problem are we actually solving?

**Plain statement:** For a liquid, tradable NSE/BSE stock, on any given trading day
*t*, estimate the probability that the stock will make an **explosive upward move**
within the next **2–10 trading days**, and surface only the high-probability,
high-conviction cases with reasoning.

This is a **cross-sectional, path-dependent, probabilistic classification** problem
with a strong **class-imbalance** (explosive moves are rare) and a strong
**tradability constraint** (India microstructure gates entry/exit).

It is explicitly **not**:
- a point price forecast (we predict *probability of a move class*, not a price),
- a "predict every stock" problem (we accept low recall for high precision),
- direction-agnostic (Phase 0 targets **upside** explosions; short-side is a later,
  separate study because borrow/short constraints in India cash are different).

---

## 2. Defining "explosive move" — the hard part

An explosive move must be defined so that it is:
1. **Statistically meaningful** — clearly separable from normal noise.
2. **Volatility-aware** — +15% means something different for a calm large-cap vs a
   jumpy small-cap.
3. **Tradable** — achievable by an actual entry/exit, not an untouchable circuit lock.
4. **Path-aware** — a stock that pops +20% then round-trips to −10% is not the same
   as one that trends to +20% cleanly; the *stop* matters.

### 2.1 Two candidate definitions (to compare in Phase 1)

**A. Absolute-threshold (simple, interpretable):**
> Explosive if `max_high[t+1 … t+H] / entry_price − 1 ≥ θ_abs` before hitting a stop,
> with `H = 10` trading days and `θ_abs` in the 15–25% band.

**B. Volatility-scaled (robust across the cap spectrum) — PREFERRED starting point:**
> Explosive if the forward move reaches `k × ATR%₂₀` (e.g. `k ≈ 2.5–3.0`) within `H`
> days before hitting a stop of `m × ATR%₂₀` (e.g. `m ≈ 1.0–1.5`),
> where `ATR%₂₀` = 20-day Average True Range as a % of price.

Volatility-scaling (B) is preferred because India's universe spans ₹50 microcaps to
₹3000 large-caps with wildly different daily ranges; a single absolute % would flood
the label with small-cap noise and starve large-caps. We will still **report** the
absolute-% distribution so definitions stay human-interpretable.

### 2.2 The labeling method: **Triple-Barrier** (López de Prado)

For each candidate entry at day *t* (entry assumed at **next day's price** to avoid
look-ahead — see §4), place three barriers over the forward window:

- **Upper barrier** (profit target): `entry × (1 + k·ATR%₂₀)` → label **+1 (explosive)**
- **Lower barrier** (stop): `entry × (1 − m·ATR%₂₀)` → label **−1 (failed)**
- **Vertical barrier** (time): day `t + H` (H ≤ 10) → label **0 (neutral / no move)**

The label is decided by **whichever barrier is touched first** (path-dependent). This
is far superior to naive "forward return sign" because it respects stops, targets, and
holding-period reality — exactly how a swing trade actually resolves.

**Why triple-barrier here specifically:** swing trades live and die by path (did the
stop hit before the target?). A fixed-horizon return label would mislabel trades that
would have been stopped out, inflating backtest performance. Triple-barrier prevents
that class of self-deception.

### 2.3 Meta-labeling (for the confidence score)

We plan a **two-stage** design:
1. **Primary model** decides *whether* a setup qualifies (the +1 vs not decision).
2. **Meta-label model** predicts *the probability the primary signal is correct* —
   this becomes the **confidence score** and drives position sizing. Meta-labeling is
   the cleanest way to produce calibrated confidence and to separate "is there a
   setup?" from "how much do I trust it?".

---

## 3. Tradability filter (India-specific — non-negotiable)

A label of +1 only counts if the trade was **actually enterable and exitable**:

- **Entry blocked if** the stock opens/locks at **upper circuit** on the intended
  entry day (can't buy), or is in **T2T** with no intraday, or under **ASM/GSM** stage
  restricting normal trading, or in the **F&O ban period** (no new positions for F&O
  names).
- **Exit realism:** if the target is only reachable via a **locked upper circuit** (no
  liquidity to sell into), we mark the fill as **unrealizable** and do not count it as
  a clean win; we model exit at the next liquid opportunity.
- **Liquidity floor (candidate, to calibrate — U3):** median 20-day turnover
  ≥ ₹1–5 crore, price ≥ ₹20, and not in a permanent illiquid/SME segment.

> Consequence: our labels are computed on a **point-in-time universe** that already
> encodes what was tradable *on that date* — never with today's knowledge.

---

## 4. Avoiding look-ahead & bias (labeling discipline)

- **Entry timing:** features are computed using data **up to and including close of day
  t**; the trade is entered at **day t+1 open (or close)**. No feature may peek at t+1.
- **Corporate actions:** use **split/bonus/dividend-adjusted** prices for returns; keep
  **unadjusted** prices for circuit/liquidity logic. Mixing these is a classic bug.
- **Survivorship:** the universe on day *t* must include stocks that were **later
  delisted/merged**; building the universe from today's listed names is survivorship
  bias and inflates results.
- **Overlapping labels:** because forward windows overlap across days, samples are not
  IID. This mandates **purged + embargoed** cross-validation (see doc 03) and
  **sample-uniqueness weighting**.
- **Point-in-time surveillance flags:** ASM/GSM/ban status must be as-of-date, not
  current.

---

## 5. Success metrics (how we judge the system)

Because this is imbalanced and precision-oriented, **accuracy is a trap**. We use:

- **Precision @ K / hit-rate on fired signals** — of the setups we flag, what fraction
  become explosive? (Primary business metric.)
- **Precision-Recall AUC** (not ROC-AUC alone) — appropriate under heavy imbalance.
- **Calibration** — Brier score + reliability curve. A "70% confidence" signal must be
  right ~70% of the time. Non-negotiable for a probability system.
- **Economic metrics** (the real test): cost-aware backtest CAGR, Sharpe/Sortino, max
  drawdown, hit-rate, average win/avg loss, profit factor, expectancy per trade —
  **after** STT, stamp duty, brokerage, slippage, and impact.
- **Regime-stratified** versions of all the above (bull/bear/sideways, high/low vol).

### 5.1 Penalizing the two error types
- **False positive** (flagged, didn't explode / stopped out): costs a real losing trade
  → penalized directly through the cost-aware backtest and precision metric.
- **False negative** (missed explosion): tracked as **opportunity cost** but weighted
  **less** — our mandate is high-probability precision, not catching everything. We
  explicitly accept low recall.

We will pick an **operating point** on the precision/recall curve that maximizes
risk-adjusted, cost-aware expectancy — not one that maximizes raw accuracy.

---

## 6. The empirical study that must happen first (Phase 1)

Before fixing any threshold, we run a **move-distribution study** on the historical
universe to answer (currently all **UNKNOWN**):
- What is the base rate of a `k·ATR` upside move within 10 days? (U4)
- How does it vary by market-cap bucket, liquidity, and regime?
- What θ / k / m give a class that is rare enough to be "explosive" but frequent enough
  to model (enough positive samples per regime)?
- How often are labeled winners actually **untradable** (circuit/T2T/ASM)?

The output of that study **replaces the placeholder numbers above with measured ones**,
and gets written back into `PROJECT_MEMORY.md` as resolved decisions.

---

## 7. Open items feeding the memory

- U2 (threshold), U3 (liquidity floor), U4 (base rate) resolved by the Phase-1 study.
- Deliverable of this doc: a **precise, testable label definition** — done at the
  *specification* level; the *numeric calibration* is Phase 1.
