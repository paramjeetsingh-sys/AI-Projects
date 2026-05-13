"""
Fetches AI news from RSS/Atom feeds using only Python stdlib
(urllib + xml.etree.ElementTree — no third-party packages needed).
"""
import re
import ssl
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional

RSS_FEEDS = [
    {"name": "TechCrunch AI",       "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI",      "url": "https://venturebeat.com/ai/feed/"},
    {"name": "MIT Technology Review","url": "https://www.technologyreview.com/feed/"},
    {"name": "The Verge AI",        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
    {"name": "Wired AI",            "url": "https://www.wired.com/feed/tag/artificial-intelligence/rss"},
    {"name": "Ars Technica",        "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "OpenAI Blog",         "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google DeepMind",     "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Hugging Face Blog",   "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "AI News",             "url": "https://www.artificialintelligence-news.com/feed/"},
    {"name": "Analytics Vidhya",    "url": "https://www.analyticsvidhya.com/feed/"},
    {"name": "Towards Data Science","url": "https://towardsdatascience.com/feed"},
    {"name": "NVIDIA Blog",         "url": "https://blogs.nvidia.com/feed/"},
    {"name": "Microsoft AI Blog",   "url": "https://blogs.microsoft.com/ai/feed/"},
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

# Atom namespace
ATOM_NS = "http://www.w3.org/2005/Atom"

_AI_SPECIFIC = {"OpenAI Blog", "Google DeepMind", "Hugging Face Blog", "NVIDIA Blog", "Microsoft AI Blog"}

_SSL_CTX = ssl.create_default_context()


def _strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_ai_related(title: str, summary: str) -> bool:
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in AI_KEYWORDS)


def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    # Try RFC 2822 (RSS pubDate)
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except Exception:
        pass
    # Try ISO 8601 (Atom published/updated)
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str[:19], fmt[:len(date_str[:19])])
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def _text(elem, tag: str, ns: str = "") -> str:
    ns_prefix = f"{{{ns}}}" if ns else ""
    child = elem.find(f"{ns_prefix}{tag}")
    return (child.text or "").strip() if child is not None else ""


def _parse_rss(root: ET.Element, cutoff: datetime, feed_name: str) -> List[Dict]:
    articles = []
    channel = root.find("channel")
    if channel is None:
        return articles
    for item in channel.findall("item"):
        title   = _text(item, "title")
        link    = _text(item, "link")
        summary = _strip_tags(_text(item, "description"))[:600]
        pub_raw = _text(item, "pubDate")
        pub_date = _parse_date(pub_raw)

        if not title or not link:
            continue
        if pub_date and pub_date < cutoff:
            continue
        if feed_name not in _AI_SPECIFIC and not _is_ai_related(title, summary):
            continue

        articles.append({
            "source":    feed_name,
            "title":     title,
            "summary":   summary,
            "link":      link,
            "published": pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else "Today",
        })
    return articles


def _parse_atom(root: ET.Element, cutoff: datetime, feed_name: str) -> List[Dict]:
    articles = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        title   = _text(entry, "title", ATOM_NS)
        # Atom <link> is an empty element with href attribute
        link_el = entry.find(f"{{{ATOM_NS}}}link")
        link    = (link_el.get("href", "") if link_el is not None else "")
        summary = _strip_tags(_text(entry, "summary", ATOM_NS) or _text(entry, "content", ATOM_NS))[:600]
        pub_raw = _text(entry, "published", ATOM_NS) or _text(entry, "updated", ATOM_NS)
        pub_date = _parse_date(pub_raw)

        if not title or not link:
            continue
        if pub_date and pub_date < cutoff:
            continue
        if feed_name not in _AI_SPECIFIC and not _is_ai_related(title, summary):
            continue

        articles.append({
            "source":    feed_name,
            "title":     title,
            "summary":   summary,
            "link":      link,
            "published": pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else "Today",
        })
    return articles


def fetch_feed(feed_info: Dict, cutoff: datetime) -> List[Dict]:
    try:
        req = urllib.request.Request(
            feed_info["url"],
            headers={"User-Agent": "Mozilla/5.0 (compatible; AINewsBot/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as resp:
            content = resp.read()

        root = ET.fromstring(content)
        tag  = root.tag.lower()

        if "rss" in tag or root.tag == "rss":
            return _parse_rss(root, cutoff, feed_info["name"])
        if ATOM_NS in root.tag or root.tag.lower() == "feed":
            return _parse_atom(root, cutoff, feed_info["name"])

        # Unknown format — try both
        articles = _parse_rss(root, cutoff, feed_info["name"])
        if not articles:
            articles = _parse_atom(root, cutoff, feed_info["name"])
        return articles

    except Exception as e:
        print(f"  [WARN] Failed to fetch {feed_info['name']}: {e}")
        return []


def fetch_all_news(lookback_hours: int = 24) -> List[Dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    all_articles: List[Dict] = []

    print(f"Fetching AI news from {len(RSS_FEEDS)} sources (last {lookback_hours}h)...")
    for feed_info in RSS_FEEDS:
        print(f"  Fetching: {feed_info['name']}")
        all_articles.extend(fetch_feed(feed_info, cutoff))
        time.sleep(0.3)

    # Deduplicate by title prefix
    seen: set = set()
    unique = []
    for a in all_articles:
        key = a["title"].lower()[:60]
        if key not in seen:
            seen.add(key)
            unique.append(a)

    print(f"Found {len(unique)} unique AI articles.")
    return unique
