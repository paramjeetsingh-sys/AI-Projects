"""
Summarizes AI news articles via LLM API using only Python stdlib (http.client).

Supported providers (auto-detected from environment):
  • Anthropic Claude  — set ANTHROPIC_API_KEY
  • Groq              — set GROQ_API_KEY  (fallback)

If neither key is set the digest is built with raw article data (no AI summary).
"""
import http.client
import json
import os
import ssl
from datetime import datetime
from typing import Dict, List

_SSL_CTX = ssl.create_default_context()

ANTHROPIC_MODEL = "claude-sonnet-4-6"
GROQ_MODEL      = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert AI journalist and curator. Analyze the AI news articles and create a structured daily digest.

Categorize into:
1. new_models        — New AI models, products, or major releases
2. research          — Academic papers, research findings, technical advances
3. features_updates  — Updates to existing AI tools, new features, improvements
4. industry_business — Funding, partnerships, acquisitions, company news
5. policy_society    — AI regulation, ethics, safety, societal impact

For each article write a 2-3 sentence summary and a "why_it_matters" note.

Return ONLY a valid JSON object — no markdown, no code fences — with this exact structure:
{
  "date": "YYYY-MM-DD",
  "total_articles": <number>,
  "headline": "<one compelling sentence about the biggest story today>",
  "tldr": "<3-4 sentence overall summary of today in AI>",
  "categories": {
    "new_models":        [{"title":"...","source":"...","link":"...","summary":"...","why_it_matters":"..."}],
    "research":          [...],
    "features_updates":  [...],
    "industry_business": [...],
    "policy_society":    [...]
  },
  "top_story": {"title":"...","source":"...","link":"...","summary":"...","why_it_matters":"..."}
}"""


# ── low-level HTTP helpers ────────────────────────────────────────────────────

def _post_json(host: str, path: str, headers: Dict, payload: Dict) -> Dict:
    body = json.dumps(payload).encode("utf-8")
    conn = http.client.HTTPSConnection(host, context=_SSL_CTX, timeout=120)
    try:
        conn.request("POST", path, body, {**headers, "Content-Length": str(len(body))})
        resp = conn.getresponse()
        raw  = resp.read().decode("utf-8")
        return json.loads(raw)
    finally:
        conn.close()


def _call_anthropic(system: str, user_msg: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    data = _post_json(
        "api.anthropic.com",
        "/v1/messages",
        {
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type":      "application/json",
        },
        {
            "model":      ANTHROPIC_MODEL,
            "max_tokens": 8192,
            "temperature": 0.3,
            "system":     system,
            "messages":   [{"role": "user", "content": user_msg}],
        },
    )
    if "error" in data:
        raise RuntimeError(f"Anthropic API error: {data['error']}")
    return data["content"][0]["text"]


def _call_groq(system: str, user_msg: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY", "")
    data = _post_json(
        "api.groq.com",
        "/openai/v1/chat/completions",
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        {
            "model":           GROQ_MODEL,
            "max_tokens":      8192,
            "temperature":     0.3,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system",  "content": system},
                {"role": "user",    "content": user_msg},
            ],
        },
    )
    if "error" in data:
        raise RuntimeError(f"Groq API error: {data['error']}")
    return data["choices"][0]["message"]["content"]


def _call_llm(system: str, user_msg: str) -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        print(f"  Using Anthropic Claude ({ANTHROPIC_MODEL})")
        return _call_anthropic(system, user_msg)
    if os.environ.get("GROQ_API_KEY"):
        print(f"  Using Groq ({GROQ_MODEL})")
        return _call_groq(system, user_msg)
    raise RuntimeError(
        "No LLM API key found. Set ANTHROPIC_API_KEY or GROQ_API_KEY in your .env file."
    )


# ── public API ────────────────────────────────────────────────────────────────

def _build_articles_text(articles: List[Dict]) -> str:
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

    today        = datetime.now().strftime("%Y-%m-%d")
    capped       = articles[:80]
    articles_txt = _build_articles_text(capped)

    print(f"Summarizing {len(capped)} articles with LLM...")
    try:
        raw = _call_llm(
            SYSTEM_PROMPT,
            (
                f"Today is {today}. Here are today's AI news articles:\n\n"
                f"{articles_txt}\n\n"
                "Create a comprehensive daily AI digest. Return ONLY valid JSON."
            ),
        )
        digest = json.loads(raw)
        digest["total_articles"] = len(articles)
        return digest
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON parse failed: {e}. Using fallback digest.")
        return _fallback_digest(articles, today)
    except Exception as e:
        print(f"[WARN] LLM summarization failed: {e}. Using fallback digest.")
        return _fallback_digest(articles, today)


def _empty_digest() -> Dict:
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_articles": 0,
        "headline": "No AI news found today.",
        "tldr": "No articles were fetched today. Check your network or RSS feed sources.",
        "categories": {k: [] for k in ("new_models", "research", "features_updates",
                                        "industry_business", "policy_society")},
        "top_story": None,
    }


def _fallback_digest(articles: List[Dict], today: str) -> Dict:
    cats: Dict[str, List] = {k: [] for k in ("new_models", "research", "features_updates",
                                               "industry_business", "policy_society")}
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
