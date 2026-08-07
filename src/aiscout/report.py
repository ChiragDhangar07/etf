"""Dashboard generator: results.json -> self-contained HTML (inline SVG charts).

Produces an institutional-style, theme-aware research dashboard. No external assets
(CSP-safe): charts are hand-built SVG, fonts are system stacks. The SYNTHETIC-data
honesty banner is rendered prominently and unconditionally when data_label != LIVE.
"""
from __future__ import annotations

import html
import json
from pathlib import Path


# ----------------------------- SVG chart helpers -----------------------------
def _svg_area(dates, values, w=920, h=260, pad=36):
    if not values:
        return "<p>no data</p>"
    lo, hi = min(values), max(values)
    rng = (hi - lo) or 1.0
    n = len(values)
    def x(i): return pad + i * (w - 2 * pad) / max(n - 1, 1)
    def y(v): return h - pad - (v - lo) / rng * (h - 2 * pad)
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(values))
    area = f"{pad},{h-pad} " + pts + f" {x(n-1):.1f},{h-pad}"
    # faint horizontal gridlines + baseline at equity=1
    grid = ""
    for frac in (0, .25, .5, .75, 1):
        gy = pad + frac * (h - 2 * pad)
        grid += f'<line x1="{pad}" y1="{gy:.1f}" x2="{w-pad}" y2="{gy:.1f}" class="grid"/>'
    base_y = y(1.0) if lo <= 1.0 <= hi else None
    base = (f'<line x1="{pad}" y1="{base_y:.1f}" x2="{w-pad}" y2="{base_y:.1f}" '
            f'class="baseline"/>') if base_y else ""
    end_x, end_y = x(n - 1), y(values[-1])
    lab_first = html.escape(str(dates[0])) if dates else ""
    lab_last = html.escape(str(dates[-1])) if dates else ""
    return f'''<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="Equity curve">
  {grid}{base}
  <polygon points="{area}" class="area"/>
  <polyline points="{pts}" class="line"/>
  <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="4.5" class="endpoint"/>
  <text x="{pad}" y="{h-8}" class="axlab">{lab_first}</text>
  <text x="{w-pad}" y="{h-8}" class="axlab" text-anchor="end">{lab_last}</text>
  <text x="{end_x-6:.1f}" y="{end_y-10:.1f}" class="endlab" text-anchor="end">{values[-1]:.2f}x</text>
</svg>'''


def _svg_reliability(pred, obs, w=380, h=300, pad=40):
    def x(v): return pad + v * (w - 2 * pad)
    def y(v): return h - pad - v * (h - 2 * pad)
    diag = f'<line x1="{x(0)}" y1="{y(0)}" x2="{x(1)}" y2="{y(1)}" class="diag"/>'
    pts = ""
    if pred:
        line = " ".join(f"{x(p):.1f},{y(o):.1f}" for p, o in zip(pred, obs))
        pts += f'<polyline points="{line}" class="rel-line"/>'
        for p, o in zip(pred, obs):
            pts += f'<circle cx="{x(p):.1f}" cy="{y(o):.1f}" r="3.5" class="rel-dot"/>'
    return f'''<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="Calibration">
  <rect x="{pad}" y="{pad}" width="{w-2*pad}" height="{h-2*pad}" class="plot"/>
  {diag}{pts}
  <text x="{w/2}" y="{h-8}" class="axlab" text-anchor="middle">predicted probability</text>
  <text x="14" y="{h/2}" class="axlab" transform="rotate(-90 14 {h/2})" text-anchor="middle">observed freq</text>
</svg>'''


def _svg_bars(items, w=380, h=300, pad=40):
    # items: list of (label, value, cls)
    if not items:
        return ""
    hi = max(v for _, v, _ in items) or 1
    bw = (w - 2 * pad) / len(items)
    bars = ""
    for i, (lab, v, cls) in enumerate(items):
        bh = (v / hi) * (h - 2 * pad)
        bx = pad + i * bw + bw * 0.18
        by = h - pad - bh
        bars += (f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw*0.64:.1f}" '
                 f'height="{bh:.1f}" class="bar {cls}"/>'
                 f'<text x="{bx+bw*0.32:.1f}" y="{by-8:.1f}" class="barval" '
                 f'text-anchor="middle">{v:.2f}x</text>'
                 f'<text x="{bx+bw*0.32:.1f}" y="{h-pad+18:.1f}" class="barlab" '
                 f'text-anchor="middle">{html.escape(lab)}</text>')
    base = f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" class="grid"/>'
    return f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="Model comparison">{base}{bars}</svg>'


# ----------------------------- HTML assembly -----------------------------
def _pill(ok: bool, good="PASS", bad="REVIEW"):
    cls = "ok" if ok else "warn"
    return f'<span class="pill {cls}">{good if ok else bad}</span>'


def _stat(label, value, sub="", tone="accent"):
    return f'''<div class="stat">
      <div class="stat-label">{html.escape(label)}</div>
      <div class="stat-value {tone}">{value}</div>
      <div class="stat-sub">{html.escape(sub)}</div>
    </div>'''


def _fmt_pct(x, d=1):
    try:
        return f"{x*100:.{d}f}%"
    except Exception:
        return "—"


def build_inner(r: dict) -> str:
    synthetic = "LIVE" not in r.get("data_label", "SYNTHETIC")
    m = r["metrics_oos"]["gbm"]
    ml = r["metrics_oos"]["logistic_baseline"]
    mr = r["metrics_oos"]["rule_baseline"]
    bt = r.get("backtest", {})
    uni = r["universe"]
    cfg = r["config"]

    banner = (f'''<div class="banner">
      <strong>SYNTHETIC DATA</strong> — the research sandbox blocks live market feeds,
      so this run uses a controlled market simulator. These numbers validate that the
      <em>pipeline</em> works and can learn signal that exists by construction. They are
      <strong>not</strong> evidence of a live-market edge. Run <code>scripts/run_live.py</code>
      where NSE/Yahoo are reachable for real results.
    </div>''' if synthetic else
    '''<div class="banner live"><strong>LIVE DATA</strong> — results computed on real
      NSE data via Yahoo Finance.</div>''')

    # KPI row
    lift = m.get("lift_at_k", float("nan"))
    kpis = "".join([
        _stat("Base rate (positives)", _fmt_pct(m["base_rate"]),
              "share of tradable setups that explode", "muted"),
        _stat("Precision @ top 10%", _fmt_pct(m["precision_at_k"]),
              f"{lift:.2f}× lift over base rate", "accent"),
        _stat("PR-AUC (OOS)", f'{m["pr_auc"]:.3f}',
              "precision-recall, imbalance-aware", "accent"),
        _stat("Brier score", f'{m["brier"]:.4f}',
              "lower = better calibrated", "muted"),
    ])
    if "error" not in bt:
        kpis += "".join([
            _stat("Backtest CAGR", _fmt_pct(bt["cagr"]),
                  "net of India costs · SYNTHETIC" if synthetic else "net of costs",
                  "good" if bt["cagr"] > 0 else "bad"),
            _stat("Sharpe", f'{bt["sharpe"]:.2f}',
                  f'maxDD {_fmt_pct(bt["max_drawdown"])}',
                  "good" if bt["sharpe"] > 1 else "muted"),
        ])

    # model comparison bars (lift over base rate)
    bars = _svg_bars([
        ("GBM", m.get("lift_at_k", 0) or 0, "b-accent"),
        ("Logistic", ml.get("lift_at_k", 0) or 0, "b-neutral"),
        ("Rule", mr.get("lift_at_k", 0) or 0, "b-neutral"),
    ])
    gbm_beats = (m.get("lift_at_k", 0) or 0) >= max(ml.get("lift_at_k", 0) or 0,
                                                    mr.get("lift_at_k", 0) or 0)

    # equity curve
    eq = bt.get("equity_curve", {})
    equity_svg = _svg_area(eq.get("dates", []), eq.get("equity", [])) if eq else "<p>—</p>"

    # reliability
    rel = r.get("reliability", {})
    rel_svg = _svg_reliability(rel.get("pred", []), rel.get("obs", []))

    # regime table
    reg_rows = ""
    for rg, mm in r.get("regime_metrics", {}).items():
        reg_rows += (f'<tr><td>{html.escape(rg)}</td>'
                     f'<td class="num">{mm["n"]}</td>'
                     f'<td class="num">{_fmt_pct(mm["base_rate"])}</td>'
                     f'<td class="num">{_fmt_pct(mm["precision_at_k"])}</td>'
                     f'<td class="num">{mm["lift_at_k"]:.2f}×</td>'
                     f'<td class="num">{mm["pr_auc"]:.3f}</td></tr>')
    if not reg_rows:
        reg_rows = '<tr><td colspan="6" class="muted">insufficient per-regime samples</td></tr>'

    # holdout
    ho = r.get("holdout", {})
    holdout_html = ""
    if "error" not in ho:
        holdout_html = (f'<p class="note">Locked out-of-sample holdout (from '
                        f'<code>{ho.get("cut_date","?")}</code>, touched once): '
                        f'precision@10% <strong>{_fmt_pct(ho["precision_at_k"])}</strong> '
                        f'({ho["lift_at_k"]:.2f}× lift), PR-AUC {ho["pr_auc"]:.3f}.</p>')

    # alerts
    alert_cards = ""
    for a in r.get("alerts", []):
        reasons = "".join(f"<li>{html.escape(x)}</li>" for x in a["reasons"])
        risks = "".join(f"<li>{html.escape(x)}</li>" for x in a["risk_factors"])
        alert_cards += f'''<article class="alert">
          <header>
            <div class="tick">{html.escape(a["symbol"])}</div>
            <div class="conf"><span>{a["confidence"]*100:.0f}%</span><small>confidence</small></div>
          </header>
          <div class="alert-grid">
            <div><span class="k">Price</span><span class="v">{a["price"]}</span></div>
            <div><span class="k">Target</span><span class="v">{a.get("target","—")}</span></div>
            <div><span class="k">Stop / invalidation</span><span class="v">{a.get("stop_invalidation","—")}</span></div>
            <div><span class="k">Reward:Risk</span><span class="v">{a.get("expected_reward_risk","—")}</span></div>
            <div><span class="k">Horizon</span><span class="v">{a["expected_timeframe_days"]}d</span></div>
            <div><span class="k">Exp. move</span><span class="v">{a.get("expected_move_pct","—")}%</span></div>
          </div>
          <div class="why"><h4>Why flagged</h4><ul>{reasons}</ul></div>
          <div class="why risk"><h4>Risk factors</h4><ul>{risks}</ul></div>
        </article>'''
    if not alert_cards:
        alert_cards = '<p class="muted">No tradable setups cleared the confidence floor on the latest day.</p>'

    pipeline = " → ".join([
        "Ingest", "Point-in-time store", "Feature engine", "Regime engine",
        "Triple-barrier labels", "Walk-forward CV", "Calibrated GBM",
        "Cost-aware backtest", "Explainable alerts",
    ])

    return f'''
<div class="wrap">
  {banner}
  <header class="masthead">
    <div>
      <div class="eyebrow">AIScout · India NSE/BSE · swing 2–10 day upside</div>
      <h1>Opportunity-Detection Engine</h1>
      <p class="lede">End-to-end research pipeline: {uni["symbols"]} symbols ×
        {uni["days"]} trading days ({html.escape(uni["date_range"][0])} →
        {html.escape(uni["date_range"][1])}), {r["n_features"]} point-in-time features,
        leakage-safe walk-forward validation, India cost model.</p>
    </div>
    <div class="verdict">
      {_pill(gbm_beats, "GBM &gt; baselines", "baseline wins")}
      <div class="verdict-sub">{cfg["top_k_per_day"]} signals/day ·
        {cfg["horizon_days"]}d barrier · embargo {cfg["embargo_days"]}d</div>
    </div>
  </header>

  <div class="pipeline">{html.escape(pipeline)}</div>

  <section class="stats">{kpis}</section>

  <section class="cols">
    <div class="card">
      <h3>Model vs. baselines <span class="hint">lift over base rate (OOS)</span></h3>
      {bars}
      <p class="note">A complex model must beat the simple ones out-of-sample to earn
        its place. Lift = precision@10% ÷ base rate.</p>
    </div>
    <div class="card">
      <h3>Calibration <span class="hint">predicted vs. observed</span></h3>
      {rel_svg}
      <p class="note">Points on the diagonal mean a “70%” signal is right ~70% of the
        time. Isotonic-calibrated.</p>
    </div>
  </section>

  <section class="card wide">
    <h3>Cost-aware equity curve
      <span class="hint">{"SYNTHETIC — machinery check, not a live edge" if synthetic else "live"}</span></h3>
    {equity_svg}
    <div class="bt-row">
      {"".join(f'<div><span class="k">{k}</span><span class="v">{v}</span></div>' for k, v in [
        ("Trades", bt.get("n_trades","—")),
        ("Hit rate", _fmt_pct(bt["hit_rate"]) if "error" not in bt else "—"),
        ("Profit factor", f'{bt["profit_factor"]:.2f}' if "error" not in bt else "—"),
        ("Avg win", _fmt_pct(bt["avg_win"]) if "error" not in bt else "—"),
        ("Avg loss", _fmt_pct(bt["avg_loss"]) if "error" not in bt else "—"),
      ])}
    </div>
  </section>

  <section class="card wide">
    <h3>Regime-stratified performance <span class="hint">an edge must survive across regimes</span></h3>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Regime</th><th class="num">n</th><th class="num">base</th>
        <th class="num">prec@10%</th><th class="num">lift</th><th class="num">PR-AUC</th></tr></thead>
      <tbody>{reg_rows}</tbody>
    </table></div>
    {holdout_html}
  </section>

  <section class="card wide">
    <h3>Latest explainable alerts <span class="hint">never a bare “buy”</span></h3>
    <div class="alerts">{alert_cards}</div>
  </section>

  <footer class="foot">
    <p><strong>Honesty:</strong> {"Synthetic-data run — validates the pipeline, not a live edge. " if synthetic else ""}All
      metrics are out-of-sample and net of the India cost model. Nothing here is investment advice.</p>
    <p class="mono">config: horizon {cfg["horizon_days"]}d · barriers {r["config"]["k_up_atr"]}×ATR up /
      {r["config"]["m_down_atr"]}×ATR stop · label positives {r["label_summary"]["n_positive"]} /
      {r["label_summary"]["labeled_samples"]} ({_fmt_pct(r["label_summary"]["positive_rate"])})</p>
  </footer>
</div>
'''


CSS = """
:root{
  --ground:#f6f8fa; --surface:#ffffff; --surface-2:#eef2f6;
  --ink:#16202b; --muted:#5c6b7a; --line:#d8e0e8;
  --accent:#0d8fa0; --accent-weak:#12a5b422;
  --good:#1f9d64; --warn:#b9781a; --bad:#d1495b;
  --mono:ui-monospace,'SF Mono','JetBrains Mono',Menlo,Consolas,monospace;
  --sans:ui-sans-serif,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
}
@media (prefers-color-scheme:dark){:root{
  --ground:#0f151c; --surface:#161e27; --surface-2:#1c2732;
  --ink:#e7eef5; --muted:#8ea0b2; --line:#26323f;
  --accent:#2bc0d4; --accent-weak:#12a5b41f;
}}
:root[data-theme="light"]{
  --ground:#f6f8fa; --surface:#ffffff; --surface-2:#eef2f6;
  --ink:#16202b; --muted:#5c6b7a; --line:#d8e0e8; --accent:#0d8fa0; --accent-weak:#12a5b422;
}
:root[data-theme="dark"]{
  --ground:#0f151c; --surface:#161e27; --surface-2:#1c2732;
  --ink:#e7eef5; --muted:#8ea0b2; --line:#26323f; --accent:#2bc0d4; --accent-weak:#12a5b41f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:28px 20px 60px}
.banner{background:linear-gradient(90deg,#d1495b18,#c9861a14);border:1px solid #d1495b55;
  border-radius:10px;padding:14px 16px;font-size:.9rem;color:var(--ink)}
.banner.live{background:var(--accent-weak);border-color:var(--accent)}
.banner code{font-family:var(--mono);font-size:.85em;background:var(--surface-2);padding:1px 5px;border-radius:4px}
.masthead{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;
  margin:26px 0 14px;flex-wrap:wrap}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);margin-bottom:6px}
h1{font-size:2rem;margin:0;letter-spacing:-.02em;text-wrap:balance}
.lede{color:var(--muted);max-width:60ch;margin:8px 0 0;font-size:.92rem}
.verdict{text-align:right}
.verdict-sub{font-family:var(--mono);font-size:.72rem;color:var(--muted);margin-top:8px}
.pill{display:inline-block;font-family:var(--mono);font-size:.72rem;font-weight:700;
  padding:4px 10px;border-radius:999px;letter-spacing:.04em}
.pill.ok{background:#1f9d6422;color:var(--good);border:1px solid #1f9d6455}
.pill.warn{background:#d1495b22;color:var(--bad);border:1px solid #d1495b55}
.pipeline{font-family:var(--mono);font-size:.72rem;color:var(--muted);background:var(--surface);
  border:1px solid var(--line);border-radius:8px;padding:10px 14px;overflow-x:auto;white-space:nowrap;margin-bottom:22px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.stat-label{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.stat-value{font-family:var(--mono);font-size:1.7rem;font-weight:600;margin:4px 0 2px;
  font-variant-numeric:tabular-nums}
.stat-value.accent{color:var(--accent)} .stat-value.good{color:var(--good)}
.stat-value.bad{color:var(--bad)} .stat-value.muted{color:var(--ink)}
.stat-sub{font-size:.74rem;color:var(--muted)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
@media (max-width:720px){.cols{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px}
.card.wide{margin-bottom:16px}
.card h3{margin:0 0 12px;font-size:1rem;display:flex;justify-content:space-between;align-items:baseline;gap:12px}
.hint{font-family:var(--mono);font-size:.68rem;color:var(--muted);font-weight:400;letter-spacing:.03em}
.note{color:var(--muted);font-size:.8rem;margin:10px 0 0}
.chart{width:100%;height:auto;display:block}
.grid{stroke:var(--line);stroke-width:1}
.baseline{stroke:var(--muted);stroke-width:1;stroke-dasharray:4 4;opacity:.6}
.area{fill:var(--accent-weak)}
.line{fill:none;stroke:var(--accent);stroke-width:2;stroke-linejoin:round}
.endpoint{fill:var(--accent)}
.endlab{fill:var(--accent);font-family:var(--mono);font-size:12px;font-weight:700}
.axlab{fill:var(--muted);font-family:var(--mono);font-size:11px}
.plot{fill:none;stroke:var(--line)}
.diag{stroke:var(--muted);stroke-dasharray:4 4;opacity:.6}
.rel-line{fill:none;stroke:var(--accent);stroke-width:2}
.rel-dot{fill:var(--accent)}
.bar{fill:var(--surface-2);stroke:var(--line)}
.bar.b-accent{fill:var(--accent)}
.barval{fill:var(--ink);font-family:var(--mono);font-size:12px;font-weight:700}
.barlab{fill:var(--muted);font-family:var(--mono);font-size:11px}
.bt-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:10px;margin-top:14px}
.bt-row .k,.alert-grid .k{display:block;font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.bt-row .v,.alert-grid .v{font-family:var(--mono);font-weight:600;font-variant-numeric:tabular-nums}
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.86rem}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
th{font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600}
td.num,th.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
.alerts{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.alert{border:1px solid var(--line);border-radius:10px;padding:14px;background:var(--surface-2)}
.alert header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.tick{font-family:var(--mono);font-weight:700;font-size:1.1rem;color:var(--accent)}
.conf{text-align:right}.conf span{font-family:var(--mono);font-size:1.3rem;font-weight:700}
.conf small{display:block;font-size:.64rem;color:var(--muted);text-transform:uppercase}
.alert-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px;margin-bottom:10px}
.why h4{margin:8px 0 4px;font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.why ul{margin:0;padding-left:16px;font-size:.82rem}
.why.risk ul{color:var(--warn)}
.foot{margin-top:26px;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:16px}
.foot .mono{font-family:var(--mono);font-size:.72rem;margin-top:8px}
"""


def render(results_path: str, out_standalone: str, out_artifact: str):
    r = json.loads(Path(results_path).read_text())
    inner = build_inner(r)
    title = "AIScout — Opportunity Detection"
    # standalone (opens locally)
    standalone = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
                  f'<meta name="viewport" content="width=device-width,initial-scale=1">'
                  f'<title>{title}</title><style>{CSS}</style></head><body>{inner}</body></html>')
    Path(out_standalone).write_text(standalone)
    # artifact body-only (Artifact wraps its own doctype/head/body)
    Path(out_artifact).write_text(f'<title>{title}</title><style>{CSS}</style>{inner}')
    return out_standalone, out_artifact


if __name__ == "__main__":
    import sys
    base = Path(__file__).resolve().parents[2]
    render(str(base / "outputs" / "results.json"),
           str(base / "outputs" / "dashboard.html"),
           str(base / "outputs" / "dashboard_artifact.html"))
    print("dashboard written")
