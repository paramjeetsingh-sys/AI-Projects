import json
import os
from typing import List, Dict
from datetime import datetime

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"

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

# Keywords for each category (used in LLM-free fallback mode)
CATEGORY_KEYWORDS = {
    "new_models": [
        "launch", "launches", "release", "releases", "new model", "introduce", "introduces",
        "unveil", "unveils", "announce", "announces", "debut", "debuting",
        "gpt-5", "gpt5", "claude 4", "gemini 2", "llama 4", "mistral", "o3", "o4",
    ],
    "research": [
        "research", "paper", "study", "findings", "breakthrough", "arxiv",
        "benchmark", "outperforms", "surpasses", "scientist", "discover",
        "experiment", "dataset", "training", "evaluation",
    ],
    "features_updates": [
        "update", "feature", "improvement", "upgrade", "version", "now supports",
        "adds", "adding", "plugin", "integration", "rolls out", "expands",
        "enhanced", "improvement", "fix", "patch",
    ],
    "industry_business": [
        "fund", "funding", "acquire", "acquisition", "partner", "partnership",
        "billion", "million", "invest", "investment", "deal", "merge", "merger",
        "startup", "valuation", "ipo", "revenue", "profit", "ceo", "hire",
        "layoff", "employee", "company", "corporation",
    ],
    "policy_society": [
        "regulation", "law", "policy", "safety", "ethics", "ban", "bans",
        "congress", "senate", "eu", "government", "legal", "court", "lawsuit",
        "rights", "bias", "harm", "risk", "concern", "impact", "society",
    ],
}


def build_articles_text(articles: List[Dict]) -> str:
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(
            f"{i}. [{a['source']}] {a['title']}\n"
            f"   URL: {a['link']}\n"
            f"   Summary: {a['summary'][:300]}\n"
        )
    return "\n".join(lines)


def _categorize_article(article: Dict) -> str:
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "features_updates"


def _categorize_by_keywords(articles: List[Dict], today: str) -> Dict:
    cats: Dict[str, List] = {
        "new_models": [], "research": [], "features_updates": [],
        "industry_business": [], "policy_society": [],
    }
    for a in articles:
        cat = _categorize_article(a)
        cats[cat].append({
            "title": a["title"],
            "source": a["source"],
            "link": a["link"],
            "summary": a["summary"][:300],
            "why_it_matters": "",
        })

    top = articles[0] if articles else None
    top_story = {
        "title": top["title"], "source": top["source"],
        "link": top["link"], "summary": top["summary"][:300],
        "why_it_matters": "",
    } if top else None

    source_list = ", ".join(sorted({a["source"] for a in articles[:5]}))
    return {
        "date": today,
        "total_articles": len(articles),
        "headline": top["title"] if top else "Today in AI",
        "tldr": (
            f"Fetched {len(articles)} AI articles today from sources including {source_list}. "
            f"Stories span new model releases, research, industry moves, and policy. "
            f"Add a GROQ_API_KEY environment variable to enable AI-powered summaries."
        ),
        "categories": cats,
        "top_story": top_story,
    }


def _summarize_with_groq(articles: List[Dict], today: str) -> Dict:
    from groq import Groq
    client = Groq()
    articles_text = build_articles_text(articles[:80])
    print(f"Summarizing {min(len(articles), 80)} articles with {MODEL} via Groq...")
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=8192,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
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
    )
    raw = response.choices[0].message.content
    try:
        digest = json.loads(raw)
        digest["total_articles"] = len(articles)
        return digest
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON parse failed: {e}. Using keyword-based fallback.")
        return _categorize_by_keywords(articles, today)


def summarize_news(articles: List[Dict]) -> Dict:
    if not articles:
        return _empty_digest()

    today = datetime.now().strftime("%Y-%m-%d")

    if GROQ_API_KEY:
        return _summarize_with_groq(articles, today)

    print("No GROQ_API_KEY found — using keyword-based categorization (set GROQ_API_KEY for AI summaries).")
    return _categorize_by_keywords(articles, today)


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
