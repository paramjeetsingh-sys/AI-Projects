import re
import xmltodict
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from email.utils import parsedate_to_datetime
import time

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

# Dedicated AI sources that don't need keyword filtering
AI_DEDICATED_SOURCES = {"OpenAI Blog", "Google DeepMind", "Hugging Face Blog", "NVIDIA Blog", "Microsoft AI Blog"}


def is_ai_related(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    # RFC 2822 (RSS pubDate)
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except Exception:
        pass
    # ISO 8601 / Atom (dateutil)
    try:
        from dateutil import parser as du
        return du.parse(date_str).astimezone(timezone.utc)
    except Exception:
        pass
    return None


def _text(val) -> str:
    """Extract a plain string from a feedparser-like xmltodict value."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return str(val.get("#text", "") or val.get("@href", ""))
    return str(val)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_rss_items(channel: dict, feed_name: str, cutoff: datetime) -> List[Dict]:
    items = channel.get("item", [])
    if isinstance(items, dict):
        items = [items]
    articles = []
    for item in items:
        pub_date = _parse_date(item.get("pubDate") or item.get("dc:date"))
        if pub_date and pub_date < cutoff:
            continue

        title = _text(item.get("title", "")).strip()
        link = _text(item.get("link", "") or item.get("guid", "")).strip()
        summary = _text(item.get("description", "") or item.get("content:encoded", ""))
        summary = _strip_html(summary)[:600]

        if not title or not link:
            continue
        if feed_name not in AI_DEDICATED_SOURCES and not is_ai_related(title, summary):
            continue

        articles.append({
            "source": feed_name,
            "title": title,
            "summary": summary,
            "link": link,
            "published": pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else "Today",
        })
    return articles


def _parse_atom_entries(feed: dict, feed_name: str, cutoff: datetime) -> List[Dict]:
    entries = feed.get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]
    articles = []
    for entry in entries:
        pub_date = _parse_date(entry.get("updated") or entry.get("published"))
        if pub_date and pub_date < cutoff:
            continue

        title = _text(entry.get("title", "")).strip()

        link = entry.get("link", "")
        if isinstance(link, list):
            link = next((l for l in link if isinstance(l, dict) and l.get("@rel") == "alternate"), link[0])
        link = _text(link).strip()

        summary = entry.get("summary", "") or entry.get("content", "")
        summary = _strip_html(_text(summary))[:600]

        if not title or not link:
            continue
        if feed_name not in AI_DEDICATED_SOURCES and not is_ai_related(title, summary):
            continue

        articles.append({
            "source": feed_name,
            "title": title,
            "summary": summary,
            "link": link,
            "published": pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else "Today",
        })
    return articles


def fetch_feed(feed_info: Dict, cutoff: datetime) -> List[Dict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AINewsBot/1.0)"}
        resp = requests.get(feed_info["url"], headers=headers, timeout=15)
        resp.raise_for_status()
        parsed = xmltodict.parse(resp.content)

        name = feed_info["name"]
        if "rss" in parsed:
            channel = parsed["rss"].get("channel", {})
            return _parse_rss_items(channel, name, cutoff)
        elif "feed" in parsed:
            return _parse_atom_entries(parsed["feed"], name, cutoff)
        elif "rdf:RDF" in parsed:
            # RDF/RSS 1.0
            channel = parsed["rdf:RDF"].get("channel", {})
            return _parse_rss_items({"item": parsed["rdf:RDF"].get("item", [])}, name, cutoff)
    except Exception as e:
        print(f"  [WARN] Failed to fetch {feed_info['name']}: {e}")
    return []


def fetch_all_news(lookback_hours: int = 24) -> List[Dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    all_articles = []

    print(f"Fetching AI news from {len(RSS_FEEDS)} sources (last {lookback_hours}h)...")
    for feed_info in RSS_FEEDS:
        print(f"  Fetching: {feed_info['name']}")
        articles = fetch_feed(feed_info, cutoff)
        all_articles.extend(articles)
        time.sleep(0.3)  # polite delay

    seen_titles: set = set()
    unique_articles = []
    for a in all_articles:
        key = a["title"].lower()[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_articles.append(a)

    print(f"Found {len(unique_articles)} unique AI articles.")
    return unique_articles
