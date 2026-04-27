import re
import anthropic
import json
from typing import List, Dict
from datetime import datetime

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an expert AI journalist and curator. Your job is to analyze a list of AI news articles and create a structured daily digest.

Categorize the articles into these sections:
1. **New Models & Launches** - New AI models, products, or major releases
2. **Research & Breakthroughs** - Academic papers, research findings, technical advances
3. **Features & Updates** - Updates to existing AI tools, new features, improvements
4. **Industry & Business** - Funding, partnerships, acquisitions, company news
5. **Policy & Society** - AI regulation, ethics, safety, societal impact

For each article:
- Write a 2-3 sentence summary capturing the key insight
- Highlight WHY it matters for someone tracking the AI landscape

Return a valid JSON object with this exact structure:
{
  "date": "YYYY-MM-DD",
  "total_articles": <number>,
  "headline": "<one compelling sentence about the biggest story today>",
  "tldr": "<3-4 sentence overall summary of today in AI>",
  "categories": {
    "new_models": [{"title": "...", "source": "...", "link": "...", "summary": "...", "why_it_matters": "..."}],
    "research": [...],
    "features_updates": [...],
    "industry_business": [...],
    "policy_society": [...]
  },
  "top_story": {"title": "...", "source": "...", "link": "...", "summary": "...", "why_it_matters": "..."}
}"""


def build_articles_text(articles: List[Dict]) -> str:
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(
            f"{i}. [{a['source']}] {a['title']}\n"
            f"   URL: {a['link']}\n"
            f"   Summary: {a['summary'][:300]}\n"
        )
    return "\n".join(lines)


def summarize_news(articles: List[Dict]) -> Dict:
    if not articles:
        return _empty_digest()

    today = datetime.now().strftime("%Y-%m-%d")
    articles_text = build_articles_text(articles[:80])  # cap at 80 articles

    print(f"Summarizing {min(len(articles), 80)} articles with Claude...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # cache system prompt
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Today is {today}. Here are today's AI news articles:\n\n"
                    f"{articles_text}\n\n"
                    "Create a comprehensive daily AI digest from these articles. "
                    "Return ONLY valid JSON, no markdown code blocks."
                ),
            }
        ],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if the model wrapped the JSON despite instructions
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw)
    if match:
        raw = match.group(1).strip()
    else:
        raw = raw.strip()

    try:
        digest = json.loads(raw)
        digest["total_articles"] = len(articles)
        return digest
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON parse failed: {e}. Using fallback digest.")
        return _fallback_digest(articles, today)


def _empty_digest() -> Dict:
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_articles": 0,
        "headline": "No AI news found today.",
        "tldr": "No articles were fetched today. Check your network or RSS feed sources.",
        "categories": {
            "new_models": [], "research": [], "features_updates": [],
            "industry_business": [], "policy_society": []
        },
        "top_story": None,
    }


def _fallback_digest(articles: List[Dict], today: str) -> Dict:
    cats = {"new_models": [], "research": [], "features_updates": [], "industry_business": [], "policy_society": []}
    for a in articles[:20]:
        item = {"title": a["title"], "source": a["source"], "link": a["link"],
                "summary": a["summary"][:200], "why_it_matters": ""}
        cats["features_updates"].append(item)
    return {
        "date": today,
        "total_articles": len(articles),
        "headline": articles[0]["title"] if articles else "Today in AI",
        "tldr": f"Fetched {len(articles)} AI articles today across major sources.",
        "categories": cats,
        "top_story": None,
    }
