# 04 — Architecture (Continuously-Thinking System)

> The charter demands a system that "never sleeps": constantly observing, updating
> probabilities, comparing to history, generating hypotheses, revising confidence — not
> a cron scanner. This doc reconciles that vision with **free/EOD data reality** and
> lays a **clean upgrade path** to intraday/live. We design the loop now; we build it in
> later phases (no production code in Phase 0).

---

## 1. Honest framing: what "continuously thinking" means on free EOD data

The *cognitive loop* (observe → hypothesize → evaluate evidence → update probability →
rank → explain → self-evaluate) is real and always-on **as a process**. Its **clock**,
however, is bounded by data:

- **Now (free/EOD):** the loop runs as a **nightly cycle** after market close + a
  **lighter pre-open cycle** using global cues. Between cycles it can still re-reason
  over cached data, run analog studies, and monitor drift. It "thinks" continuously
  over a world that *updates* end-of-day.
- **Later (broker feed):** the same loop is re-clocked to **intraday** (minute bars,
  live OI) with no architectural rewrite — only the ingestion cadence and feature
  freshness change. The upgrade path is designed in from the start.

We will not market EOD data as real-time. The architecture is **cadence-agnostic** so
the promise ("intelligent analyst that never sleeps") is honestly realized at the
resolution the data allows, and improves as data improves.

---

## 2. Component map

```
                    ┌──────────────────────────────────────────────┐
                    │          MARKET INTELLIGENCE LOOP            │
                    └──────────────────────────────────────────────┘

 ┌────────────┐   ┌────────────┐   ┌───────────────┐   ┌────────────────┐
 │ INGESTION  │──▶│ POINT-IN-  │──▶│ FEATURE ENGINE │──▶│ MARKET-STATE / │
 │ (bhavcopy, │   │ TIME STORE │   │ (cross-section │   │ REGIME ENGINE  │
 │  Yahoo,    │   │ + quality  │   │  + time-series │   │ (HMM/rules,    │
 │  broker,   │   │  gates,    │   │  + analogs +   │   │  VIX, breadth, │
 │  flows,    │   │  corp-act  │   │  anomaly)      │   │  FII/DII)      │
 │  events)   │   │  adjust)   │   └──────┬─────────┘   └──────┬─────────┘
 └────────────┘   └────────────┘          │                    │
                                          ▼                    ▼
                              ┌───────────────────────────────────────┐
                              │  AI INFERENCE ENGINE (primary model)   │
                              │  + META-LABEL (confidence) + CALIBRATE │
                              └──────────────────┬────────────────────┘
                                                 ▼
                    ┌────────────┐   ┌───────────────┐   ┌────────────────┐
                    │ PROBABILITY│──▶│ RANKING ENGINE │──▶│ ALERT ENGINE   │
                    │  ENGINE    │   │ (cross-section │   │ (explainable,  │
                    │ (calibrated│   │  rank, risk    │   │  evidence,     │
                    │  P + conf) │   │  filter, dedup)│   │  invalidation) │
                    └────────────┘   └───────────────┘   └───────┬────────┘
                                                                 ▼
   ┌───────────────┐   ┌────────────────┐   ┌────────────────┐   ┌──────────────┐
   │ RISK ENGINE   │   │ PAPER-TRADE /  │   │ PERFORMANCE &  │   │ LEARNING     │
   │ (sizing, expo,│◀─▶│ SIGNAL LEDGER  │──▶│ DRIFT MONITOR  │──▶│ ENGINE       │
   │  circuit/T2T/ │   │ (track every   │   │ (calibration,  │   │ (retrain,    │
   │  ASM/ban gate)│   │  signal→outcome│   │  regime, drift)│   │  reweight,   │
   └───────────────┘   └────────────────┘   └────────────────┘   │  threshold)  │
                                                                 └──────────────┘
             ▲                                                          │
             └──────────────── model registry + config + logs ◀────────┘
```

---

## 3. Components (responsibilities)

1. **Ingestion** — pull bhavcopy (OHLCV + delivery), Yahoo/broker prices, FII/DII, OI/
   PCR, ban/ASM/GSM lists, bulk/block deals, corporate announcements, macro cues.
   Redundant sources; polite/cached; scheduled (nightly + pre-open).
2. **Point-in-time store** — the leak-prevention heart. Corporate-action adjustment,
   quality gates (bad ticks/missing files quarantined), as-of-date snapshots so any past
   date is reconstructable exactly as it was known then.
3. **Feature engine** — computes doc-02 features; cross-sectional/sector normalization;
   anomaly & historical-analog features. Strictly point-in-time.
4. **Market-state / regime engine** — classifies market regime (trend/range, vol
   bucket, FII/DII risk-on/off, breadth). Signals are interpreted *conditional on
   regime*; models can be regime-specialized.
5. **AI inference engine** — primary model → setup probability; **meta-label** →
   confidence; **calibration** layer → honest probabilities.
6. **Probability engine** — maintains calibrated P and confidence per name; updates each
   cycle; can blend with **historical-analog base rates** (Bayesian-style updating).
7. **Ranking engine** — cross-sectional ranking, de-duplication (avoid correlated
   clones), risk-aware ordering; produces the shortlist.
8. **Risk engine** — position sizing (confidence- & volatility-scaled), exposure/sector
   caps, and the **tradability gate** (drop locked-circuit/T2T/ASM/ban names). Sizing
   from meta-label confidence + expected reward/risk.
9. **Alert engine** — emits the rich alert (see §4), never a bare "buy."
10. **Paper-trade / signal ledger** — records every signal with full context and tracks
    its realized outcome (the ground truth for self-improvement).
11. **Performance & drift monitor** — live precision, calibration, regime breakdown,
    feature/label drift; raises retrain/investigate triggers.
12. **Learning engine** — periodic retraining, ensemble-weight updates, threshold
    re-tuning — always **validated** (doc 03) before promotion; versioned in the model
    registry. No silent auto-promotion of unvalidated models.
13. **Model registry + config + logging** — versioned models, reproducible configs, full
    audit trail (every signal traceable to model version + inputs).

---

## 4. Alert schema (the contract — never just "buy")

Every alert carries:
`ticker · timestamp · current price · signal type · calibrated probability ·
confidence score · reasoning (top SHAP drivers + rule trace) · supporting evidence
(RVOL, delivery%, OI/PCR, RS, breakout, flow) · risk factors · invalidation conditions
(price/level/time that kills the thesis) · expected timeframe (2–10d) · historical
analogs (N similar setups; M exploded) · suggested position size · expected volatility ·
expected reward/risk · tradability status (circuit/T2T/ASM/ban).`

Reasoning and invalidation are **mandatory** — an alert must be explainable and
falsifiable.

---

## 5. Self-improvement loop

`signal → ledger → realized outcome → performance/drift monitor → learning engine →
(validated) retrain / reweight / re-threshold → registry → back into inference`.
Every promotion passes the doc-03 gates. The system asks each cycle: *did signals
succeed? why/why not? can thresholds/features/models/weights improve?* — and only
adopts changes that validate out-of-sample.

---

## 6. Tech posture (indicative, not committed yet)

- **Language:** Python (pandas/polars, scikit-learn, LightGBM/XGBoost, SHAP) for
  research; storage as **partitioned Parquet + DuckDB/SQLite** for the point-in-time
  store (free, local, fast). Orchestration via a simple scheduler now (nightly job),
  upgradeable to a streaming/queue design when a live feed is added.
- **Reproducibility:** config-driven experiments, seeds fixed, model+data versioned.
- **Cost:** everything above is free/open-source, matching D3.

Concrete tech choices are finalized at the start of Phase 1/3, not locked in Phase 0.

---

## 7. Build order (maps to the roadmap)
Ingestion + point-in-time store (P1) → feature engine + labels (P2) → baseline model +
validation harness + cost-aware backtest (P3) → regime engine, ranking, ablation/
iteration (P4) → alert engine + drift monitor + nightly loop (P5) → paper-trade ledger +
learning engine (P6) → hardening (P7). Nothing ships to "production" before its
validation gate is passed.
