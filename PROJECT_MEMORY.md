# PROJECT MEMORY — Single Source of Truth

> This file is the canonical, continuously-maintained memory for the project.
> Every working session reads this first and continues from here. Nothing important
> is ever lost. When the conversation compresses, this file survives.

Last updated: 2026-08-06 · Phase: **0 — Research Foundation**

---

## 0. Mission

Design, research, validate, and eventually build an AI-powered **stock opportunity
detection system** that identifies **high-probability, explosive moves before they
occur**, emits **calibrated probability + confidence scores** with full reasoning,
and **continuously learns and self-improves**.

We are NOT trying to predict every stock. We are trying to find the *minority of
situations where the probability becomes significantly favorable*, and surface them
early with evidence.

This is explicitly **not** a static screener, a set of if/else filters, or a cron
scanner. It is designed as a continuously-thinking market-intelligence loop that
observes, updates probabilities, compares to history, detects anomalies, and revises
confidence.

---

## 1. LOCKED DECISIONS (do not re-litigate unless the user changes them)

| # | Decision | Value | Date |
|---|----------|-------|------|
| D1 | Market / universe | **India — NSE/BSE cash equities** | 2026-08-06 |
| D2 | Target move horizon | **Swing: multi-day, 2–10 trading days** | 2026-08-06 |
| D3 | Data budget (current) | **Free sources only** (upgrade path designed in) | 2026-08-06 |
| D4 | End use (current) | **Research + paper trading first** (live/execution later) | 2026-08-06 |
| D5 | Process order | Research → Design → Validate → Prototype → Benchmark → Production | 2026-08-06 |
| D6 | Honesty rule | Facts / hypotheses / assumptions / validated / unknown always labeled | 2026-08-06 |

**Implications of the locked decisions (consequences we must respect):**
- Free data ⇒ the system is **end-of-day (EOD) first**. True real-time tick
  microstructure is NOT available for free in India. "Continuously thinking" is
  realized initially as a **nightly research + re-scoring loop** (after close +
  bhavcopy), extensible to intraday only if/when a broker feed is added. We will be
  honest about this and never pretend to have data we don't.
- India cash equities ⇒ we MUST model India-specific microstructure that changes
  tradability: **circuit filters (2/5/10/20% price bands)**, **T2T (trade-to-trade)
  segment**, **ASM/GSM surveillance stages**, **F&O ban-period**, **T+1 settlement**,
  and **STT/stamp/brokerage costs**. A predicted move that we cannot enter (locked
  upper circuit, T2T, ASM) is worthless — tradability is part of the label.
- India free data has a **real, underused edge**: **delivery %** (deliverable qty /
  traded qty from bhavcopy), **FII/DII daily flows**, **bulk/block deals**, **F&O OI
  / PCR**, and **promoter pledge / SAST disclosures**. These are genuinely accessible
  and genuinely informative — US-centric playbooks ignore them.
- Swing 2–10 day horizon ⇒ **daily bars are the primary resolution**; features are
  cross-sectional + time-series on daily data; labels use a **triple-barrier** scheme
  over a ≤10-day vertical barrier.

---

## 2. Current project state (rolling)

**Phases 0–3 — Research Foundation + working end-to-end prototype (DONE, on synthetic data)**

Completed:
- Locked D1–D6 (see above).
- Authored the research foundation under `docs/` (00 problem+labeling, 01 data,
  02 features, 03 models+validation, 04 architecture).
- Built the full **AIScout** pipeline in `src/aiscout/` and ran it end-to-end:
  data → 29 point-in-time features → triple-barrier labels (+ tradability gate) →
  purged/embargoed walk-forward → rule/logistic/GBM + **ensemble** (calibrated) →
  regime-stratified metrics → locked holdout → India cost-aware backtest →
  explainable alerts → self-contained HTML dashboard (`report.py`).
- **Demonstration run (SYNTHETIC data, 120×1200):** ensemble is the production
  scorer at **OOS lift 1.54×** (ROC 0.60), beating logistic 1.51×, rule 1.34×,
  GBM 1.33×; **locked holdout lift 1.58×**; edge present in **all regimes**
  (bear 1.52× / bull 1.48× / sideways 1.65×); cost-aware backtest equity 1.00→1.35
  but **thin post-cost** (Sharpe 0.44, PF 1.07, maxDD −39%) — an honest lesson that
  modest lift barely survives costs with naïve sizing.
- Live adapter (`data/yahoo.py`) + `scripts/run_live.py` ready for real NSE data
  where the network permits (the dev sandbox blocks market hosts → demo is synthetic).

**CRITICAL HONESTY NOTE:** All quantitative results to date are on a **synthetic
market simulator I control**. They prove the pipeline works and can learn signal
*that exists by construction*. They are **NOT** evidence of a real-market edge.
Real performance is UNKNOWN until `run_live.py` is run on genuine NSE history.

Dashboard: `outputs/dashboard.html` (+ Artifact URL in changelog).

Not yet started (next): real-data ingestion + point-in-time store (U1/A4),
empirical move-distribution study to replace PLACEHOLDER thresholds (U2–U4),
bhavcopy/delivery + FII-DII + OI enrichment, meta-labeling, drift monitor,
paper-trade ledger.

---

## 3. Open questions / unknowns (tracked)

- **U1 — Data reliability:** NSE's public endpoints are anti-bot and fragile. We must
  decide the ingestion backbone (direct bhavcopy archives vs a free broker API such as
  Upstox/Fyers). *Leaning: bhavcopy archives for EOD history + a free broker API for
  robustness.* To validate empirically in Phase 1.
- **U2 — Explosive threshold:** Absolute (e.g. +15–20%) vs volatility-scaled (e.g.
  ≥2.5× 20d ATR%). To be set by the Phase-1 move-distribution study, not guessed.
- **U3 — Universe size / liquidity floor:** min turnover to guarantee tradability
  (candidate: median daily turnover ≥ ₹1–5 cr, price ≥ ₹20, exclude T2T/ASM-restricted
  at entry). To calibrate empirically.
- **U4 — Base rate of explosive moves:** unknown until measured; determines class
  imbalance and how we penalize false positives.
- **U5 — Do free options (OI/PCR) add signal for swing?** Hypothesis, unvalidated.

---

## 4. Risk register

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R1 | Look-ahead / leakage (overlapping labels, survivorship, corp-action adjust) | High | Purged+embargoed CV, point-in-time universe, adjusted prices, triple-barrier |
| R2 | Free data breaks / rate-limits / ToS | High | Redundant sources, local caching, respectful scraping, broker-API fallback |
| R3 | Overfitting on noisy, low-signal data | High | Walk-forward, OOS holdout, ablations, calibration, simple-model-first |
| R4 | Untradable predictions (circuit/T2T/ASM/ban) | High | Tradability filter baked into label + universe |
| R5 | Regime dependence (bull-only edge) | Medium | Regime-stratified validation (bull/bear/sideways/high-low vol) |
| R6 | Transaction costs erase edge | Medium | Cost model (STT, stamp, brokerage, slippage, impact) in every backtest |
| R7 | Scope creep / hype (DL before baseline earns it) | Medium | Baseline-first; complex models must beat simple ones on OOS to earn inclusion |

---

## 5. Assumptions (all challengeable)

- A1: Rigor > speed (user-stated).
- A2: Paper-trading fidelity is enough for now; live execution/latency deferred.
- A3: EOD cadence is acceptable for a 2–10 day horizon (entry at next-day open/close).
- A4: We can obtain reliable adjusted daily OHLCV + delivery data for a liquid NSE
  universe on free tiers. (To be proven in Phase 1 — this is the make/break assumption.)

---

## 6. Communication contract (every response)

Each substantive response includes: (1) current understanding, (2) what was completed,
(3) what was learned, (4) remaining unknowns, (5) risks, (6) assumptions, (7)
recommended next step. Facts vs hypotheses vs assumptions vs validated vs unknown are
always distinguished. No fabricated results, ever.

---

## 7. Phased roadmap (living)

- **Phase 0 — Research foundation** *(current)*: problem def, labeling, data map,
  feature catalog, model+validation plan, architecture. → docs only, no production code.
- **Phase 1 — Data & empirics**: build ingestion, point-in-time universe, run the
  move-distribution study, finalize thresholds (U2–U4), assemble a clean dataset.
- **Phase 2 — Labeling & features**: implement triple-barrier labels + feature engine;
  audit for leakage.
- **Phase 3 — Baseline model + validation harness**: GBM baseline, purged/embargoed
  walk-forward, calibration, cost-aware backtest. Establish the bar to beat.
- **Phase 4 — Iteration**: feature discovery, ablations, regime tests, alternative
  models (only if they beat baseline OOS).
- **Phase 5 — Continuously-thinking system**: nightly loop, ranking, explainable
  alerts, drift monitoring, self-evaluation.
- **Phase 6 — Paper trading + self-improvement**: live paper signals, performance
  tracking, retraining pipeline.
- **Phase 7 — Production hardening** *(only after validation)*.

---

## 8. Changelog

- 2026-08-06: Project kicked off. D1–D6 locked. Phase 0 research foundation authored.
- 2026-08-06: Built full AIScout pipeline (`src/aiscout/`), ran end-to-end on
  synthetic data, produced HTML dashboard. Key honest result: ensemble OOS lift
  ~1.5× that generalizes to a locked holdout and across regimes, but a thin
  post-cost backtest. Dashboard Artifact:
  https://claude.ai/code/artifact/58815698-c6d4-4a30-8df0-b1a2cf753cfb
  Discovered + fixed a validation perf bug (np.isin on datetimes → integer date
  codes). Sandbox blocks live market feeds, so the demo is synthetic; `run_live.py`
  targets real NSE data elsewhere.
