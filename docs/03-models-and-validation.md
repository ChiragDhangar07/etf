# 03 — Models & Validation

> An honest survey of model families for this specific problem (imbalanced,
> cross-sectional, path-dependent, noisy, small-signal, daily), and — more importantly
> — the **leakage-safe validation protocol** that decides what we keep. On low
> signal-to-noise financial data, **validation discipline matters more than model
> choice.**

---

## 1. Model families — fit for THIS problem

| Family | Fit here | Pros | Cons | Verdict |
|--------|----------|------|------|---------|
| **Rule-based / heuristic** | Baseline & sanity | Transparent, zero-overfit, encodes domain priors (RVOL+squeeze+delivery%) | Rigid, no probability calibration, misses interactions | **Keep as the baseline to beat.** |
| **Logistic / regularized linear** | Simple probabilistic baseline | Calibrated-ish, interpretable, fast | Misses non-linearities/interactions | **Baseline #2.** |
| **Gradient-Boosted Trees (LightGBM / XGBoost / CatBoost)** | **Primary candidate** | Best-in-class on tabular financial features, handles mixed/missing, non-linear, fast, feature importance, monotonic constraints | Can overfit noise; needs careful CV | **Lead model.** |
| **Random Forest** | Robust ensemble | Low-variance, simple, good importances | Usually trails boosting | Useful cross-check. |
| **Anomaly detection (Isolation Forest, Mahalanobis, autoencoder)** | Complementary | Unsupervised, flags "unusual today," few labels needed | Not directly predictive of *direction* | **Use as a feature + hypothesis generator**, not the decider. |
| **Bayesian / probabilistic** | Calibration & uncertainty | Honest uncertainty, priors, small-data friendly | Heavier to build/scale | Selective use for calibration & regime priors. |
| **Hidden Markov / regime models** | Market-state layer | Clean regime segmentation for stratified models | Assumptions rigid | **Use for the regime engine**, not the stock signal. |
| **LSTM / Temporal CNN** | Sequence modeling | Captures temporal shape | Data-hungry, overfits low-signal daily data, hard to calibrate | **Defer** — must beat GBM OOS to earn inclusion. |
| **Transformers (temporal / cross-sectional)** | Advanced | Powerful with scale, cross-sectional attention | Very data/compute hungry, overfit risk, opaque | **Research-only later**, evidence-gated. |
| **Graph models (GNN)** | Relational (sector/supply-chain/correlation) | Encodes cross-stock structure | Complex, fragile, data-heavy | **Exploratory much later.** |
| **Reinforcement Learning** | Sizing/execution | Optimizes sequential decisions | Sample-inefficient, unstable, easy to fool yourself | **Only if justified** post-validation; not for signal generation. |
| **Ensemble / stacking** | Combine survivors | Usually best final performer | Complexity, leakage risk in stacking | **Assemble only from OOS-validated members.** |

### The evidence-based stance
For daily, cross-sectional, low-signal tabular data with limited positive samples,
**gradient-boosted trees are the honest lead**, with rule-based + logistic baselines to
beat. Deep sequence/graph/RL models are **hypotheses that must out-perform the baseline
out-of-sample and after costs** before they earn a place. We will not adopt complexity
for its own sake. `[This is a documented empirical regularity, not a guarantee for our
data — we still test it.]`

### Two-stage design (recap from doc 00)
- **Stage 1 (primary):** GBM/rules → is this an explosive setup?
- **Stage 2 (meta-label):** GBM → P(primary is correct) = **confidence score** →
  position sizing. Meta-labeling gives clean, separable calibration.

---

## 2. Validation protocol — the part that actually protects us

Financial ML fails mostly through **leakage and overfitting**, not weak models. The
protocol below is mandatory for every experiment.

### 2.1 Respect non-IID, overlapping labels
- **Purged K-Fold + embargo** (López de Prado): remove training samples whose label
  window overlaps the validation window (**purge**), and drop a buffer after each
  validation block (**embargo**). Without this, overlapping 10-day labels leak.
- **Sample-uniqueness weighting:** down-weight overlapping labels so concurrent samples
  don't count as independent evidence.

### 2.2 Walk-forward, out-of-sample, time-ordered
- **Walk-forward** (expanding or rolling): train on past, validate on the *next*
  unseen block, roll forward. This mirrors live use and is our primary evidence.
- A final **locked out-of-sample holdout** (most recent period) is touched **once**, at
  the end — never used for tuning. If we tune on it, it's gone.
- **Combinatorial Purged CV** later for more robust path statistics.

### 2.3 Point-in-time everything
- Universe, features, labels, surveillance flags all **as-of-date**. No survivorship,
  no restatement leakage (R1).

### 2.4 Regime-stratified evaluation
- Report all metrics **separately** for bull / bear / sideways and high / low VIX. A
  system that only works in bull markets must be **known** to only work in bull
  markets. Regime robustness > headline average.

### 2.5 Calibration is a first-class test
- **Brier score + reliability curve**; apply **isotonic / Platt** calibration on a
  held-out fold. A "70%" must mean ~70%. An uncalibrated probability system is
  dishonest by construction.

### 2.6 Robustness battery
- **Ablation studies** — drop feature groups, measure OOS delta → what actually carries
  signal (guards against decorative features).
- **Sensitivity analysis** — vary thresholds (k, m, H), costs, universe floor; a fragile
  edge that only exists at one setting is not an edge.
- **Stress tests** — crash windows (2020 COVID, 2008-analog if data allows), high-vol
  spikes, low-liquidity periods.
- **False-positive / false-negative deep-dives** — categorize failures to drive feature
  and threshold improvement.
- **Drift detection** — monitor feature and performance drift over time; trigger
  retraining/alerts (feeds doc 04's learning engine).

### 2.7 Cost-aware from day one
Every economic result is **net of** STT, exchange charges, stamp duty, SEBI/GST,
brokerage, plus a **slippage + market-impact model** (worse for small-caps/thin names).
A pre-cost edge is not an edge.

---

## 3. What "good enough to proceed" looks like (gates)

A model/feature graduates to the next phase only if, **out-of-sample and after costs**:
1. It **beats the rule-based + logistic baselines** on precision-oriented and economic
   metrics.
2. It is **calibrated** (reliability curve within tolerance; acceptable Brier).
3. It is **robust across regimes** (no single-regime dependence hidden in the average).
4. It **survives ablation & sensitivity** (edge isn't a single-knob artifact).
5. Its edge **survives realistic costs and slippage**.

Anything failing these is rejected or sent back — no exceptions. This is how we avoid
fooling ourselves.

---

## 4. Explainability requirement
Because alerts must carry *reasoning* (charter requirement), we bias toward models we
can explain: tree models + **SHAP** feature attributions, rule traces, and
historical-analog evidence. A black box that can't justify a signal is not shippable for
this project’s alerting mandate.
