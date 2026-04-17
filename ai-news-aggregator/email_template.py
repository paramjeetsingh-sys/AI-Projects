from typing import Dict, List


def _category_section(title: str, emoji: str, articles: List[Dict], accent: str) -> str:
    if not articles:
        return ""

    rows = ""
    for a in articles:
        why = f'<p style="margin:6px 0 0;font-size:13px;color:#6b7280;font-style:italic;">{a.get("why_it_matters","")}</p>' if a.get("why_it_matters") else ""
        rows += f"""
        <div style="padding:14px 0;border-bottom:1px solid #f3f4f6;">
          <div style="display:flex;align-items:flex-start;gap:10px;">
            <div style="flex:1;">
              <a href="{a['link']}" style="font-size:15px;font-weight:600;color:#111827;text-decoration:none;line-height:1.4;"
                 onmouseover="this.style.color='{accent}'" onmouseout="this.style.color='#111827'">{a['title']}</a>
              <div style="margin-top:4px;">
                <span style="font-size:11px;font-weight:600;color:{accent};background:{accent}18;padding:2px 8px;border-radius:20px;">{a['source']}</span>
              </div>
              <p style="margin:8px 0 0;font-size:14px;color:#374151;line-height:1.6;">{a['summary']}</p>
              {why}
            </div>
          </div>
        </div>"""

    return f"""
    <div style="background:#ffffff;border-radius:12px;padding:20px 24px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <h2 style="margin:0 0 4px;font-size:18px;color:{accent};">{emoji} {title}</h2>
      <div style="height:2px;background:linear-gradient(90deg,{accent},transparent);border-radius:2px;margin-bottom:12px;"></div>
      {rows}
    </div>"""


def build_html_email(digest: Dict) -> str:
    date_str = digest.get("date", "Today")
    headline = digest.get("headline", "Today in AI")
    tldr = digest.get("tldr", "")
    total = digest.get("total_articles", 0)
    top_story = digest.get("top_story")
    cats = digest.get("categories", {})

    # Top story block
    top_html = ""
    if top_story:
        top_html = f"""
    <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:12px;padding:24px;margin-bottom:24px;color:#fff;">
      <div style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;opacity:0.8;margin-bottom:8px;">⭐ Top Story</div>
      <a href="{top_story['link']}" style="font-size:20px;font-weight:700;color:#fff;text-decoration:none;line-height:1.4;display:block;">{top_story['title']}</a>
      <div style="margin-top:6px;">
        <span style="font-size:11px;font-weight:600;background:rgba(255,255,255,0.2);padding:2px 10px;border-radius:20px;">{top_story['source']}</span>
      </div>
      <p style="margin:12px 0 0;font-size:14px;line-height:1.6;opacity:0.95;">{top_story['summary']}</p>
      {f'<p style="margin:8px 0 0;font-size:13px;opacity:0.85;font-style:italic;">{top_story.get("why_it_matters","")}</p>' if top_story.get("why_it_matters") else ""}
    </div>"""

    sections = (
        _category_section("New Models & Launches", "🚀", cats.get("new_models", []), "#7c3aed") +
        _category_section("Research & Breakthroughs", "🔬", cats.get("research", []), "#0891b2") +
        _category_section("Features & Updates", "✨", cats.get("features_updates", []), "#059669") +
        _category_section("Industry & Business", "💼", cats.get("industry_business", []), "#d97706") +
        _category_section("Policy & Society", "⚖️", cats.get("policy_society", []), "#dc2626")
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>AI Daily Digest – {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#f8f9fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">

  <!-- Preheader -->
  <div style="display:none;max-height:0;overflow:hidden;color:#f8f9fc;">{headline} | {total} articles curated for you today.</div>

  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fc;padding:32px 16px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

        <!-- Header -->
        <tr><td>
          <div style="background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);border-radius:16px 16px 0 0;padding:32px 32px 28px;text-align:center;">
            <div style="font-size:28px;margin-bottom:6px;">🤖</div>
            <h1 style="margin:0;font-size:26px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">AI Daily Digest</h1>
            <p style="margin:8px 0 0;font-size:14px;color:#a5b4fc;">{date_str}</p>
            <div style="margin-top:16px;background:rgba(255,255,255,0.08);border-radius:8px;padding:12px 20px;">
              <p style="margin:0;font-size:15px;color:#e2e8f0;line-height:1.5;font-style:italic;">"{headline}"</p>
            </div>
          </div>
        </td></tr>

        <!-- Stats Bar -->
        <tr><td>
          <div style="background:#1e1b4b;padding:12px 32px;display:flex;justify-content:center;">
            <div style="display:flex;gap:32px;justify-content:center;">
              <div style="text-align:center;color:#c7d2fe;">
                <div style="font-size:22px;font-weight:700;color:#a5b4fc;">{total}</div>
                <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;">Articles</div>
              </div>
              <div style="width:1px;background:rgba(255,255,255,0.1);"></div>
              <div style="text-align:center;color:#c7d2fe;">
                <div style="font-size:22px;font-weight:700;color:#a5b4fc;">{len([v for v in cats.values() if v])}</div>
                <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;">Categories</div>
              </div>
              <div style="width:1px;background:rgba(255,255,255,0.1);"></div>
              <div style="text-align:center;color:#c7d2fe;">
                <div style="font-size:22px;font-weight:700;color:#a5b4fc;">15+</div>
                <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;">Sources</div>
              </div>
            </div>
          </div>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:24px 0;">

          <!-- TL;DR -->
          <div style="background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:20px;border-left:4px solid #7c3aed;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
            <h3 style="margin:0 0 8px;font-size:13px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#7c3aed;">📋 TL;DR — Today at a Glance</h3>
            <p style="margin:0;font-size:15px;color:#374151;line-height:1.7;">{tldr}</p>
          </div>

          {top_html}
          {sections}

        </td></tr>

        <!-- Footer -->
        <tr><td>
          <div style="background:#1e1b4b;border-radius:0 0 16px 16px;padding:24px 32px;text-align:center;">
            <p style="margin:0 0 8px;font-size:13px;color:#a5b4fc;">🤖 Curated by AI News Aggregator · Powered by Claude</p>
            <p style="margin:0;font-size:12px;color:#6366f1;">Sources: TechCrunch, VentureBeat, MIT Tech Review, The Verge, Wired, OpenAI, DeepMind, Hugging Face & more</p>
            <p style="margin:12px 0 0;font-size:11px;color:#4f46e5;">This digest is automatically generated daily and sent to paramjeet.singh@classplus.co</p>
          </div>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def build_plain_text_email(digest: Dict) -> str:
    date_str = digest.get("date", "Today")
    headline = digest.get("headline", "")
    tldr = digest.get("tldr", "")
    total = digest.get("total_articles", 0)
    cats = digest.get("categories", {})
    top_story = digest.get("top_story")

    lines = [
        f"AI DAILY DIGEST — {date_str}",
        "=" * 50,
        f"\n{headline}",
        f"\nTotal articles curated: {total}",
        f"\nTL;DR:\n{tldr}",
    ]

    if top_story:
        lines += [f"\n⭐ TOP STORY: {top_story['title']}",
                  f"Source: {top_story['source']}",
                  f"Link: {top_story['link']}",
                  f"{top_story['summary']}"]

    cat_map = [
        ("🚀 NEW MODELS & LAUNCHES", cats.get("new_models", [])),
        ("🔬 RESEARCH & BREAKTHROUGHS", cats.get("research", [])),
        ("✨ FEATURES & UPDATES", cats.get("features_updates", [])),
        ("💼 INDUSTRY & BUSINESS", cats.get("industry_business", [])),
        ("⚖️ POLICY & SOCIETY", cats.get("policy_society", [])),
    ]

    for title, articles in cat_map:
        if articles:
            lines.append(f"\n{title}")
            lines.append("-" * 40)
            for a in articles:
                lines += [f"\n• {a['title']}",
                          f"  Source: {a['source']}",
                          f"  {a['summary']}",
                          f"  {a['link']}"]

    lines.append("\n" + "=" * 50)
    lines.append("Powered by Claude AI · AI News Aggregator")
    return "\n".join(lines)
