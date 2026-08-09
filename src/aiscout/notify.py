"""Email notifications for AIScout alerts.

Sends the day's ranked shortlist to your inbox via SMTP. Credentials come ONLY from
environment variables -- never hard-code them:

    SMTP_HOST      e.g. smtp.gmail.com
    SMTP_PORT      e.g. 587            (STARTTLS) or 465 (SSL)
    SMTP_USER      your sending address
    SMTP_PASS      an app password (for Gmail: create an "App Password")
    ALERT_EMAIL_TO where to send (defaults to SMTP_USER)

Usage:
    from aiscout.notify import email_alerts
    email_alerts(results)                      # reads env for creds
    # or dry-run (no send), just get the HTML:
    html = build_email_html(results)
"""
from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def build_email_html(results: dict) -> str:
    r = results
    synthetic = "LIVE" not in r.get("data_label", "SYNTHETIC")
    alerts = r.get("alerts", [])
    uni = r.get("universe", {})
    prod = r.get("production_model", "model")
    banner = ("" if not synthetic else
              '<div style="background:#fdecec;border:1px solid #d1495b;padding:10px 12px;'
              'border-radius:8px;color:#7a2230;font-size:13px;margin-bottom:14px">'
              '<b>SYNTHETIC DATA</b> — demo run, not a live-market signal. '
              'Run on real data to get real alerts.</div>')

    rows = ""
    for a in alerts:
        reasons = "; ".join(a.get("reasons", [])[:3])
        rows += f"""<tr>
          <td style="padding:8px;border-bottom:1px solid #e5e9ee"><b>{a['symbol']}</b></td>
          <td style="padding:8px;border-bottom:1px solid #e5e9ee;text-align:right">{a['price']}</td>
          <td style="padding:8px;border-bottom:1px solid #e5e9ee;text-align:right;color:#0d8fa0">
            <b>{int(a['confidence']*100)}%</b></td>
          <td style="padding:8px;border-bottom:1px solid #e5e9ee;text-align:right">{a.get('target','—')}</td>
          <td style="padding:8px;border-bottom:1px solid #e5e9ee;text-align:right">{a.get('stop_invalidation','—')}</td>
          <td style="padding:8px;border-bottom:1px solid #e5e9ee;font-size:12px;color:#4a5765">{reasons}</td>
        </tr>"""
    if not rows:
        rows = ('<tr><td colspan="6" style="padding:12px;color:#5c6b7a">'
                'No setups cleared the confidence floor today.</td></tr>')

    return f"""<!doctype html><html><body style="font-family:Arial,Helvetica,sans-serif;
      color:#16202b;max-width:720px;margin:0 auto;padding:16px">
      {banner}
      <h2 style="margin:0 0 4px">AIScout — today's opportunity shortlist</h2>
      <p style="color:#5c6b7a;font-size:13px;margin:0 0 14px">
        Universe: {uni.get('symbols','?')} stocks · model: {prod} ·
        horizon {r.get('config',{}).get('horizon_days','?')} trading days.
        Probabilities are estimates, not certainties. Not investment advice.</p>
      <table style="border-collapse:collapse;width:100%;font-size:14px">
        <thead><tr style="text-align:left;color:#5c6b7a;font-size:12px">
          <th style="padding:8px">Stock</th><th style="padding:8px;text-align:right">Price</th>
          <th style="padding:8px;text-align:right">Confidence</th>
          <th style="padding:8px;text-align:right">Target</th>
          <th style="padding:8px;text-align:right">Stop</th>
          <th style="padding:8px">Why</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="color:#8ea0b2;font-size:11px;margin-top:16px">
        Each alert has a target and a stop (invalidation). Manage risk; a stop hit means
        the idea was wrong. Circuit-locked / T2T / ASM names are excluded as untradable.</p>
    </body></html>"""


def email_alerts(results: dict, subject: str | None = None,
                 to: str | None = None) -> bool:
    """Send the alerts email using SMTP creds from the environment. Returns True on send."""
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASS")
    to = to or os.environ.get("ALERT_EMAIL_TO") or user
    if not (host and user and pw and to):
        raise RuntimeError(
            "Missing SMTP env vars. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, "
            "ALERT_EMAIL_TO (see aiscout/notify.py docstring).")

    n = len(results.get("alerts", []))
    tag = "" if "LIVE" in results.get("data_label", "") else "[DEMO] "
    subject = subject or f"{tag}AIScout: {n} opportunity alert(s) today"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    msg.attach(MIMEText(build_email_html(results), "html"))

    ctx = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ctx) as s:
            s.login(user, pw)
            s.sendmail(user, [to], msg.as_string())
    else:
        with smtplib.SMTP(host, port) as s:
            s.starttls(context=ctx)
            s.login(user, pw)
            s.sendmail(user, [to], msg.as_string())
    return True
