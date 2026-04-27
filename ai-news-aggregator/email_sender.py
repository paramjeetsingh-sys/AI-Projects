"""
Sends the daily AI digest as a formatted HTML email via SMTP.

Required environment variables:
  EMAIL_FROM      — sender address (e.g. you@gmail.com)
  EMAIL_PASSWORD  — SMTP password / Gmail App Password
  EMAIL_TO        — recipient address (comma-separated for multiple)

Optional:
  SMTP_HOST  — defaults to smtp.gmail.com
  SMTP_PORT  — defaults to 587 (STARTTLS)
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List


# ── SMTP config from environment ──────────────────────────────────────────────
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_TO_RAW = os.environ.get("EMAIL_TO", "")


# ── HTML helpers ──────────────────────────────────────────────────────────────

CATEGORY_LABELS = {
    "new_models":        "🚀 New Models & Launches",
    "research":          "🔬 Research & Breakthroughs",
    "features_updates":  "⚙️  Features & Updates",
    "industry_business": "💼 Industry & Business",
    "policy_society":    "⚖️  Policy & Society",
}

CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #f4f6f9; margin: 0; padding: 0; color: #1a1a2e; }
.wrapper { max-width: 680px; margin: 24px auto; }
.header  { background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
           border-radius: 12px 12px 0 0; padding: 32px 28px; color: #fff; }
.header h1 { margin: 0 0 4px; font-size: 22px; font-weight: 700; }
.header .date { font-size: 13px; opacity: .75; }
.tldr  { background: #e8f4fd; border-left: 4px solid #2196f3;
         padding: 16px 20px; margin: 0; font-size: 14px; line-height: 1.7; }
.top-story { background: #fff3e0; border-left: 4px solid #ff9800;
             padding: 16px 20px; margin: 12px 0 0; }
.top-story h2 { margin: 0 0 8px; font-size: 13px; text-transform: uppercase;
                letter-spacing: .06em; color: #e65100; }
.top-story .title a { font-size: 16px; font-weight: 700; color: #1a1a2e;
                      text-decoration: none; }
.top-story .why { font-size: 13px; color: #555; margin-top: 6px; }
.section { background: #fff; margin-top: 12px; border-radius: 8px;
           box-shadow: 0 1px 4px rgba(0,0,0,.07); overflow: hidden; }
.section-head { padding: 12px 20px; font-size: 14px; font-weight: 700;
                background: #f9f9fc; border-bottom: 1px solid #eee; }
.article { padding: 14px 20px; border-bottom: 1px solid #f0f0f0; }
.article:last-child { border-bottom: none; }
.article .title a { font-size: 14px; font-weight: 600; color: #0f3460;
                    text-decoration: none; }
.article .meta { font-size: 11px; color: #999; margin: 3px 0 6px; }
.article .summary { font-size: 13px; color: #444; line-height: 1.6; }
.article .why { font-size: 12px; color: #777; margin-top: 5px;
                font-style: italic; }
.footer { text-align: center; padding: 20px; font-size: 11px; color: #aaa; }
"""


def _article_html(art: Dict) -> str:
    title = art.get("title", "Untitled")
    link  = art.get("link", "#")
    source = art.get("source", "")
    summary = art.get("summary", "")
    why = art.get("why_it_matters", "")
    why_block = f'<div class="why">💡 {why}</div>' if why else ""
    return (
        f'<div class="article">'
        f'<div class="title"><a href="{link}">{title}</a></div>'
        f'<div class="meta">{source}</div>'
        f'<div class="summary">{summary}</div>'
        f'{why_block}'
        f'</div>'
    )


def _section_html(key: str, articles: List[Dict]) -> str:
    if not articles:
        return ""
    label = CATEGORY_LABELS.get(key, key.replace("_", " ").title())
    items = "".join(_article_html(a) for a in articles)
    return (
        f'<div class="section">'
        f'<div class="section-head">{label}</div>'
        f'{items}'
        f'</div>'
    )


def build_html(digest: Dict) -> str:
    date    = digest.get("date", "")
    total   = digest.get("total_articles", 0)
    headline = digest.get("headline", "Today in AI")
    tldr    = digest.get("tldr", "")
    cats    = digest.get("categories", {})
    top     = digest.get("top_story")

    top_html = ""
    if top:
        top_html = (
            f'<div class="top-story">'
            f'<h2>Top Story</h2>'
            f'<div class="title"><a href="{top.get("link","#")}">{top.get("title","")}</a></div>'
            f'<div class="meta">{top.get("source","")}</div>'
            f'<div class="summary">{top.get("summary","")}</div>'
            f'<div class="why">💡 {top.get("why_it_matters","")}</div>'
            f'</div>'
        )

    sections_html = ""
    for key in ("new_models", "research", "features_updates", "industry_business", "policy_society"):
        sections_html += _section_html(key, cats.get(key, []))

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>{CSS}</style></head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="date">{date} · {total} articles</div>
    <h1>{headline}</h1>
  </div>
  <div class="tldr">{tldr}</div>
  {top_html}
  {sections_html}
  <div class="footer">AI Daily Digest · Powered by Groq (Llama 3.3 70B) · Unsubscribe by removing the cron job.</div>
</div>
</body>
</html>"""


def build_plain(digest: Dict) -> str:
    date     = digest.get("date", "")
    headline = digest.get("headline", "Today in AI")
    tldr     = digest.get("tldr", "")
    cats     = digest.get("categories", {})
    total    = digest.get("total_articles", 0)

    lines = [
        f"AI Daily Digest — {date}",
        f"Articles found: {total}",
        "=" * 60,
        headline,
        "",
        tldr,
        "",
    ]
    for key, label in CATEGORY_LABELS.items():
        articles = cats.get(key, [])
        if not articles:
            continue
        lines.append(label)
        lines.append("-" * len(label))
        for a in articles:
            lines.append(f"• {a.get('title','')}  ({a.get('source','')})")
            lines.append(f"  {a.get('link','')}")
            if a.get("summary"):
                lines.append(f"  {a['summary'][:160]}")
            lines.append("")
    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def send_digest_email(digest: Dict) -> bool:
    """
    Send digest via SMTP. Returns True on success, False on failure.
    Reads EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO (and optional SMTP_*) from env.
    """
    if not EMAIL_FROM or not EMAIL_PASSWORD or not EMAIL_TO_RAW:
        print("[EMAIL] Skipped — EMAIL_FROM / EMAIL_PASSWORD / EMAIL_TO not set.")
        return False

    recipients = [r.strip() for r in EMAIL_TO_RAW.split(",") if r.strip()]
    date = digest.get("date", "today")
    subject = f"AI Daily Digest — {date}: {digest.get('headline', '')[:80]}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = ", ".join(recipients)

    msg.attach(MIMEText(build_plain(digest), "plain", "utf-8"))
    msg.attach(MIMEText(build_html(digest),  "html",  "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, recipients, msg.as_string())
        print(f"[EMAIL] Digest sent to {', '.join(recipients)}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")
        return False
