import json
import os
from datetime import datetime
from typing import Optional
from eval_runner import SessionResult


def _score_color(score: float) -> str:
    if score >= 8:
        return "#22c55e"
    if score >= 6:
        return "#f59e0b"
    if score >= 4:
        return "#f97316"
    return "#ef4444"


def _score_badge(score: Optional[float], label: str = "") -> str:
    if score is None or score < 0:
        return f'<span class="badge na">N/A{" " + label if label else ""}</span>'
    color = _score_color(score)
    return (
        f'<span class="badge" style="background:{color}">'
        f'{score:.1f}{" " + label if label else ""}</span>'
    )


def generate_html_report(results: list[SessionResult], output_path: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    valid = [r for r in results if not r.error or r.overall_score > 0]

    avg_overall = (
        sum(r.overall_score for r in valid) / len(valid) if valid else 0
    )
    avg_accuracy = (
        sum(r.accuracy.score for r in valid if r.accuracy) /
        max(1, sum(1 for r in valid if r.accuracy))
    )
    avg_engagement = (
        sum(r.engagement.score for r in valid if r.engagement) /
        max(1, sum(1 for r in valid if r.engagement))
    )
    ts_valid = [r for r in valid if r.topic_shift and r.topic_shift.score >= 0]
    avg_topic_shift = (
        sum(r.topic_shift.score for r in ts_valid) / len(ts_valid) if ts_valid else None
    )

    rows_html = ""
    for r in results:
        acc_badge = _score_badge(r.accuracy.score if r.accuracy else None)
        eng_badge = _score_badge(r.engagement.score if r.engagement else None)
        ts_score = r.topic_shift.score if r.topic_shift else None
        ts_badge = _score_badge(ts_score)
        overall_badge = _score_badge(r.overall_score)
        error_cell = f'<td class="error-cell">{r.error or ""}</td>'

        acc_detail = ""
        if r.accuracy and r.accuracy.issues:
            issues = "".join(f"<li>{i}</li>" for i in r.accuracy.issues[:3])
            acc_detail = f"<ul class='issues'>{issues}</ul>"

        eng_detail = ""
        if r.engagement and r.engagement.issues:
            issues = "".join(f"<li>{i}</li>" for i in r.engagement.issues[:3])
            eng_detail = f"<ul class='issues'>{issues}</ul>"

        ts_detail = ""
        if r.topic_shift and r.topic_shift.extra.get("repetition_instances", 0) > 0:
            rep = r.topic_shift.extra.get("repetition_instances", 0)
            shifts = r.topic_shift.extra.get("successful_shifts", 0)
            ts_detail = f"<small>{rep} repetitions, {shifts} successful shifts</small>"

        rows_html += f"""
        <tr>
            <td><code>{r.user_id}</code></td>
            <td><code>{r.session_id}</code></td>
            <td class="center">{r.message_count}</td>
            <td class="center">{acc_badge}{acc_detail}</td>
            <td class="center">{eng_badge}{eng_detail}</td>
            <td class="center">{ts_badge}{ts_detail}</td>
            <td class="center">{overall_badge}</td>
            {error_cell}
        </tr>"""

    ts_stat = f"{avg_topic_shift:.1f}/10" if avg_topic_shift is not None else "N/A"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Evals Report — {timestamp}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
  h1 {{ font-size: 1.8rem; font-weight: 700; color: #f8fafc; margin-bottom: 4px; }}
  .subtitle {{ color: #94a3b8; margin-bottom: 32px; font-size: 0.9rem; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px; margin-bottom: 32px; }}
  .stat-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px;
               padding: 20px; text-align: center; }}
  .stat-card .label {{ font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;
                      letter-spacing: 0.05em; margin-bottom: 8px; }}
  .stat-card .value {{ font-size: 2rem; font-weight: 700; }}
  .table-wrap {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px;
                overflow: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
  th {{ background: #0f172a; color: #94a3b8; padding: 12px 16px; text-align: left;
       font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;
       border-bottom: 1px solid #334155; white-space: nowrap; }}
  td {{ padding: 12px 16px; border-bottom: 1px solid #1e293b; vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #0f172a; }}
  .center {{ text-align: center; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-weight: 700;
           font-size: 0.85rem; color: white; }}
  .badge.na {{ background: #475569; }}
  .issues {{ margin-top: 6px; padding-left: 16px; font-size: 0.75rem; color: #94a3b8; }}
  .issues li {{ margin-bottom: 2px; }}
  .error-cell {{ color: #f87171; font-size: 0.75rem; max-width: 200px; }}
  code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px;
         font-family: monospace; font-size: 0.8rem; color: #7dd3fc; }}
  small {{ color: #94a3b8; font-size: 0.75rem; display: block; margin-top: 4px; }}
  h2 {{ font-size: 1.2rem; color: #f8fafc; margin-bottom: 16px; }}
</style>
</head>
<body>
<div class="container">
  <h1>AI Evals Platform — Conversation Quality Report</h1>
  <p class="subtitle">Generated: {timestamp} &nbsp;|&nbsp; {len(results)} sessions evaluated</p>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="label">Sessions Evaluated</div>
      <div class="value" style="color:#7dd3fc">{len(results)}</div>
    </div>
    <div class="stat-card">
      <div class="label">Overall Score</div>
      <div class="value" style="color:{_score_color(avg_overall)}">{avg_overall:.1f}<span style="font-size:1rem;color:#94a3b8">/10</span></div>
    </div>
    <div class="stat-card">
      <div class="label">Avg Accuracy</div>
      <div class="value" style="color:{_score_color(avg_accuracy)}">{avg_accuracy:.1f}<span style="font-size:1rem;color:#94a3b8">/10</span></div>
    </div>
    <div class="stat-card">
      <div class="label">Avg Engagement</div>
      <div class="value" style="color:{_score_color(avg_engagement)}">{avg_engagement:.1f}<span style="font-size:1rem;color:#94a3b8">/10</span></div>
    </div>
    <div class="stat-card">
      <div class="label">Avg Topic Shifting</div>
      <div class="value" style="color:{'#94a3b8' if avg_topic_shift is None else _score_color(avg_topic_shift)}">{ts_stat}</div>
    </div>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>User ID</th>
          <th>Session ID</th>
          <th>Messages</th>
          <th>Accuracy</th>
          <th>Engagement</th>
          <th>Topic Shifting</th>
          <th>Overall</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def generate_json_report(results: list[SessionResult], output_path: str) -> str:
    timestamp = datetime.now().isoformat()
    valid = [r for r in results if r.overall_score > 0]

    summary = {
        "generated_at": timestamp,
        "total_sessions": len(results),
        "avg_overall": round(sum(r.overall_score for r in valid) / max(1, len(valid)), 2),
        "avg_accuracy": round(
            sum(r.accuracy.score for r in valid if r.accuracy) /
            max(1, sum(1 for r in valid if r.accuracy)), 2
        ),
        "avg_engagement": round(
            sum(r.engagement.score for r in valid if r.engagement) /
            max(1, sum(1 for r in valid if r.engagement)), 2
        ),
    }

    ts_valid = [r for r in valid if r.topic_shift and r.topic_shift.score >= 0]
    if ts_valid:
        summary["avg_topic_shift"] = round(
            sum(r.topic_shift.score for r in ts_valid) / len(ts_valid), 2
        )

    output = {
        "summary": summary,
        "sessions": [r.to_dict() for r in results],
    }

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return output_path
