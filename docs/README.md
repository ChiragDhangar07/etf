# Research Foundation — Index

This directory is the **Phase 0** deliverable: the deep-research groundwork we lay
*before* any production code. It is written for India NSE/BSE cash equities, a swing
(2–10 day) explosive-move target, on free data, for research + paper trading first.

Read `../PROJECT_MEMORY.md` first — it is the single source of truth. These docs
expand its research sections.

## Documents

| Doc | Purpose |
|-----|---------|
| [00 — Problem Definition & Labeling](00-problem-definition-and-labeling.md) | Precise, statistically-valid definition of an "explosive move" and how we turn it into labels. The most important doc. |
| [01 — Data Sources (India, free)](01-data-sources-india.md) | What data actually exists on free tiers, how reliable/legal it is, and what each source unlocks. |
| [02 — Feature Catalog](02-feature-catalog.md) | Candidate predictive variables, organized by category and data tier, with hypotheses. |
| [03 — Models & Validation](03-models-and-validation.md) | Honest survey of model families and a leakage-safe validation protocol. |
| [04 — Architecture](04-architecture.md) | The continuously-thinking system design, sized to free/EOD reality with an upgrade path. |

## Guiding principles (from the project charter)

1. **Research first.** No production code until problem, data, labels, and validation
   are pinned down.
2. **Nothing is accepted without validation.** Walk-forward, out-of-sample, regime,
   ablation, calibration.
3. **Honesty over hype.** If something can't be predicted reliably on the data we
   have, we say so and explain why.
4. **Tradability is part of truth.** A move we can't enter (locked circuit, T2T, ASM,
   F&O ban) does not count as a win.
5. **Simple before complex.** A model must beat the simpler baseline out-of-sample to
   earn its place.

## Status

Phase 0 in progress. Next: Phase 1 (data ingestion + empirical move-distribution
study to fix thresholds). See the roadmap in `PROJECT_MEMORY.md §7`.
