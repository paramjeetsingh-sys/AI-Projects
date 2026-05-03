import json
import os
import requests
from typing import List, Dict
from datetime import datetime

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

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
    articles_text = build_articles_text(articles[:80])

    print(f"Summarizing {min(len(articles), 80)} articles with {MODEL} via Groq...")

    if not GROQ_API_KEY:
        print("[WARN] GROQ_API_KEY not set. Using fallback digest.")
        return _fallback_digest(articles, today)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "max_tokens": 8192,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Today is {today}. Here are today's AI news articles:\n\n"
                    f"{articles_text}\n\n"
                    "Create a comprehensive daily AI digest from these articles. "
                    "Return ONLY valid JSON, no markdown code blocks."
                ),
            },
        ],
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        digest = json.loads(raw)
        digest["total_articles"] = len(articles)
        return digest
    except requests.HTTPError as e:
        print(f"[WARN] Groq API error {e.response.status_code}: {e.response.text[:300]}")
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON parse failed: {e}. Using fallback digest.")
    except Exception as e:
        print(f"[WARN] Summarizer error: {e}")

    return _fallback_digest(articles, today)


def _empty_digest() -> Dict:
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_articles": 0,
        "headline": "No AI news found today.",
        "tldr": "No articles were fetched today. Check your network or RSS feed sources.",
        "categories": {
            "new_models": [], "research": [], "features_updates": [],
            "industry_business": [], "policy_society": [],
        },
        "top_story": None,
    }


def _fallback_digest(articles: List[Dict], today: str) -> Dict:
    cats = {"new_models": [], "research": [], "features_updates": [], "industry_business": [], "policy_society": []}
    for a in articles[:20]:
        cats["features_updates"].append({
            "title": a["title"], "source": a["source"], "link": a["link"],
            "summary": a["summary"][:200], "why_it_matters": "",
        })
    return {
        "date": today,
        "total_articles": len(articles),
        "headline": articles[0]["title"] if articles else "Today in AI",
        "tldr": f"Fetched {len(articles)} AI articles today across major sources.",
        "categories": cats,
        "top_story": None,
    }
