import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional
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

_AI_SPECIFIC = {"OpenAI Blog", "Google DeepMind", "Hugging Face Blog", "NVIDIA Blog", "Microsoft AI Blog"}

# XML namespaces used by Atom / RSS extensions
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "media": "http://search.yahoo.com/mrss/",
}


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_ai_related(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _parse_date(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None
    text = text.strip()
    # RFC-2822 (RSS pubDate)
    try:
        dt = parsedate_to_datetime(text)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    # ISO-8601 / Atom
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text[:25], fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
    return None


def _text(el: Optional[ET.Element]) -> str:
    if el is None:
        return ""
    return (el.text or "").strip()


def _parse_rss(root: ET.Element, feed_name: str, cutoff: datetime) -> List[Dict]:
    articles = []
    channel = root.find("channel")
    items = (channel.findall("item") if channel is not None else []) or root.findall(".//item")
    for item in items:
        title = _text(item.find("title"))
        link = _text(item.find("link")) or _text(item.find("guid"))
        pub_raw = (_text(item.find("pubDate"))
                   or _text(item.find("dc:date", _NS))
                   or _text(item.find("{http://purl.org/dc/elements/1.1/}date")))
        desc = (_text(item.find("description"))
                or _text(item.find("content:encoded", _NS))
                or _text(item.find("{http://purl.org/rss/1.0/modules/content/}encoded")))
        pub_date = _parse_date(pub_raw)
        if pub_date and pub_date < cutoff:
            continue
        summary = _strip_html(desc)[:600]
        if not title or not link:
            continue
        if feed_name not in _AI_SPECIFIC and not is_ai_related(title, summary):
            continue
        articles.append({
            "source": feed_name,
            "title": title,
            "summary": summary,
            "link": link,
            "published": pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else "Today",
        })
    return articles


def _parse_atom(root: ET.Element, feed_name: str, cutoff: datetime) -> List[Dict]:
    articles = []
    ns = "http://www.w3.org/2005/Atom"
    for entry in root.findall(f"{{{ns}}}entry"):
        title = _text(entry.find(f"{{{ns}}}title"))
        link_el = entry.find(f"{{{ns}}}link[@rel='alternate']") or entry.find(f"{{{ns}}}link")
        link = (link_el.get("href", "") if link_el is not None else "")
        pub_raw = (_text(entry.find(f"{{{ns}}}published"))
                   or _text(entry.find(f"{{{ns}}}updated")))
        summary_el = entry.find(f"{{{ns}}}summary") or entry.find(f"{{{ns}}}content")
        desc = _text(summary_el) if summary_el is not None else ""
        pub_date = _parse_date(pub_raw)
        if pub_date and pub_date < cutoff:
            continue
        summary = _strip_html(desc)[:600]
        if not title or not link:
            continue
        if feed_name not in _AI_SPECIFIC and not is_ai_related(title, summary):
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
        root = ET.fromstring(resp.content)
        tag = root.tag.lower()
        if "rss" in tag or root.find("channel") is not None or root.find(".//item") is not None:
            return _parse_rss(root, feed_info["name"], cutoff)
        if "feed" in tag or "atom" in tag.lower():
            return _parse_atom(root, feed_info["name"], cutoff)
        # Try both as fallback
        articles = _parse_rss(root, feed_info["name"], cutoff)
        if not articles:
            articles = _parse_atom(root, feed_info["name"], cutoff)
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

    seen_titles: set = set()
    unique_articles = []
    for a in all_articles:
        key = a["title"].lower()[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_articles.append(a)

    print(f"Found {len(unique_articles)} unique AI articles.")
    return unique_articles
