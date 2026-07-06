# 13 · Alpha & Edge Detection (Indian Stocks)

Find under‑exploited, structurally‑ or behaviourally‑driven edges specific to
Indian markets.

---

## Prompt

```
Identify under-exploited opportunities and edges in [MARKET: e.g. Nifty stocks /
Bank Nifty options / Indian mid & small caps].

Focus on:
- Behavioural inefficiencies (retail crowding, anchoring, herding into hot
  sectors/IPOs, over-reaction to news, expiry-day emotion, round-number bias).
- Market-structure gaps specific to India:
    * Expiry dynamics (weekly index options, monthly stock F&O, physical
      settlement squeezes).
    * FII/DII flow footprints and index-rebalance (Nifty/Sensex reconstitution)
      front-running.
    * Liquidity/impact gaps in mid & small caps that larger funds can't access.
    * Corporate-action, block-deal, and bulk/insider-filing signals (SAST/SEBI
      disclosures).
    * Pre-open session and opening-auction quirks; MWPL / ban-period effects in
      F&O stocks.
    * Cash-futures basis, cost-of-carry and calendar-spread mispricings.

Then propose:
- 2 UNIQUE, specific strategies that exploit these edges (not generic "buy the
  dip"). Give exact triggers and instruments.
- WHY most traders miss them (structural constraints, capacity limits,
  attention, career risk, data access).
- How to EXECUTE each step by step: data needed & where to get it, entry/exit
  rules, risk controls, position sizing, and realistic capacity (₹) before the
  edge decays.
- Honest capacity & decay note: which edges shrink as they get crowded, and how
  to know when yours has stopped working.

Be rigorous: for each claimed edge, state how you'd TEST it on historical Indian
data before believing it, and what would disprove it.
```

---

### Tips
- The best genuinely‑retail‑accessible Indian edges tend to live in **liquidity
  and expiry microstructure** and **small‑cap neglect** — push the model to be
  specific and testable, and reject any "edge" it can't tell you how to falsify.
- Always demand the **capacity** estimate — an edge that only works on ₹2 lakh
  isn't worth building infra for.
