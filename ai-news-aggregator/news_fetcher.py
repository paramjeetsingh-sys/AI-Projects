import re
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

import requests
import xmltodict
from dateutil import parser as dateutil_parser

RSS_FEEDS = [
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/ai/feed/"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
    {"name": "Wired AI", "url": "https://www.wired.com/feed/tag/artificial-intelligence/rss"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "AI News (artificialintelligence-news.com)", "url": "https://www.artificialintelligence-news.com/feed/"},
    {"name": "Analytics Vidhya", "url": "https://www.analyticsvidhya.com/feed/"},
    {"name": "Towards Data Science", "url": "https://towardsdatascience.com/feed"},
    {"name": "InfoQ AI/ML", "url": "https://feed.infoq.com/"},
    {"name": "NVIDIA Blog", "url": "https://blogs.nvidia.com/feed/"},
    {"name": "Microsoft AI Blog", "url": "https://blogs.microsoft.com/ai/feed/"},
]

AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    "llm", "large language model", "gpt", "claude", "gemini", "llama", "mistral",
    "openai", "anthropic", "google deepmind", "meta ai", "microsoft ai", "nvidia ai",
    "chatgpt", "copilot", "ai model", "generative ai", "foundation model", "transformer",
    "diffusion model", "multimodal", "rag", "fine-tuning", "ai agent", "ai assistant",
    "stable diffusion", "midjourney", "dall-e", "sora", "gemma", "grok", "perplexity",
    "ai research", "ai safety", "ai regulation", "agi", "robotics", "hugging face",
]

AI_SPECIFIC_SOURCES = {
    "OpenAI Blog", "Google DeepMind", "Hugging Face Blog", "NVIDIA Blog", "Microsoft AI Blog"
}


def is_ai_related(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _strip_ns(key: str) -> str:
    """Remove XML namespace URI ({uri}local) and prefix (ns:local) from a key."""
    if not isinstance(key, str):
        return key
    key = key.split("}")[-1]
    if ":" in key and not key.startswith("@"):
        key = key.split(":")[-1]
    return key


def _normalize(obj):
    """Recursively strip namespace prefixes from all dict keys."""
    if isinstance(obj, dict):
        return {_strip_ns(k): _normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize(i) for i in obj]
    return obj


def _parse_date(val) -> Optional[datetime]:
    if not val:
        return None
    try:
        dt = dateutil_parser.parse(str(val))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _get_text(val) -> str:
    if isinstance(val, dict):
        return val.get("#text") or ""
    return str(val) if val is not None else ""


def _get_link(val) -> str:
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return val.get("@href") or val.get("#text") or ""
    if isinstance(val, list):
        for item in val:
            if isinstance(item, dict) and item.get("@rel", "alternate") == "alternate":
                return item.get("@href", "")
        if val:
            return _get_link(val[0])
    return ""


def _ensure_list(val) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]


def _parse_entry(entry: dict, source_name: str) -> Optional[Dict]:
    if not isinstance(entry, dict):
        return None

    title = _get_text(entry.get("title", "")).strip()
    link = _get_link(entry.get("link", "")).strip()

    summary = ""
    for key in ("summary", "description", "content", "encoded"):
        v = entry.get(key)
        if v:
            summary = _get_text(v)
            break

    summary = re.sub(r"<[^>]+>", " ", summary).strip()
    summary = re.sub(r"\s+", " ", summary)[:600]

    pub_date = None
    for key in ("pubDate", "published", "updated", "date"):
        v = entry.get(key)
        if v:
            pub_date = _parse_date(_get_text(v) or v)
            if pub_date:
                break

    return {
        "source": source_name,
        "title": title,
        "summary": summary,
        "link": link,
        "published": pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else "Today",
        "_pub_date": pub_date,
    }


def fetch_feed(feed_info: Dict, cutoff: datetime) -> List[Dict]:
    articles = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AINewsBot/1.0)"}
        resp = requests.get(feed_info["url"], headers=headers, timeout=15)
        resp.raise_for_status()

        raw = xmltodict.parse(resp.content)
        data = _normalize(raw)

        entries = []
        if "rss" in data:
            channel = data["rss"].get("channel", {}) or {}
            entries = _ensure_list(channel.get("item"))
        elif "feed" in data:
            entries = _ensure_list(data["feed"].get("entry"))

        for entry in entries:
            parsed = _parse_entry(entry, feed_info["name"])
            if not parsed:
                continue

            pub_date = parsed.pop("_pub_date", None)
            if pub_date and pub_date < cutoff:
                continue

            if not parsed["title"] or not parsed["link"]:
                continue

            if feed_info["name"] not in AI_SPECIFIC_SOURCES:
                if not is_ai_related(parsed["title"], parsed["summary"]):
                    continue

            articles.append(parsed)

    except Exception as e:
        print(f"  [WARN] Failed to fetch {feed_info['name']}: {e}")

    return articles


def fetch_all_news(lookback_hours: int = 24) -> List[Dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    all_articles = []

    print(f"Fetching AI news from {len(RSS_FEEDS)} sources (last {lookback_hours}h)...")
    for feed_info in RSS_FEEDS:
        print(f"  Fetching: {feed_info['name']}")
        articles = fetch_feed(feed_info, cutoff)
        all_articles.extend(articles)
        time.sleep(0.3)

    seen_titles: set = set()
    unique_articles = []
    for a in all_articles:
        key = a["title"].lower()[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_articles.append(a)

    print(f"Found {len(unique_articles)} unique AI articles.")
    return unique_articles
