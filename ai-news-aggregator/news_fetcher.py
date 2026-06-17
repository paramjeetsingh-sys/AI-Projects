import re
import requests
import xml.etree.ElementTree as ET
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

AI_SPECIFIC_SOURCES = {"OpenAI Blog", "Google DeepMind", "Hugging Face Blog", "NVIDIA Blog", "Microsoft AI Blog"}

NS = {
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


def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    date_str = date_str.strip()
    # Try RFC 2822 (RSS pubDate)
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
    except Exception:
        pass
    # Try ISO 8601 (Atom)
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str[:25], fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def _text(el, tag: str, ns: str = "") -> str:
    child = el.find(f"{ns}{tag}" if ns else tag)
    return (child.text or "").strip() if child is not None else ""


def _parse_rss_feed(root: ET.Element, feed_info: Dict, cutoff: datetime) -> List[Dict]:
    articles = []
    channel = root.find("channel")
    if channel is None:
        return articles
    for item in channel.findall("item"):
        title = _text(item, "title")
        link = _text(item, "link") or _text(item, "guid")
        pub_date_raw = _text(item, "pubDate") or _text(item, "dc:date", "{http://purl.org/dc/elements/1.1/}")
        pub_date = _parse_date(pub_date_raw)
        if pub_date and pub_date < cutoff:
            continue
        # Summary from description or content:encoded
        desc = _text(item, "description")
        content_el = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
        raw_summary = (content_el.text if content_el is not None and content_el.text else desc) or ""
        summary = _strip_html(raw_summary)[:600]

        if not title or not link:
            continue
        if feed_info["name"] not in AI_SPECIFIC_SOURCES:
            if not is_ai_related(title, summary):
                continue
        articles.append({
            "source": feed_info["name"],
            "title": title,
            "summary": summary,
            "link": link,
            "published": pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else "Today",
        })
    return articles


def _parse_atom_feed(root: ET.Element, feed_info: Dict, cutoff: datetime) -> List[Dict]:
    articles = []
    ns_atom = "http://www.w3.org/2005/Atom"
    for entry in root.findall(f"{{{ns_atom}}}entry"):
        title_el = entry.find(f"{{{ns_atom}}}title")
        title = (title_el.text or "").strip() if title_el is not None else ""

        link_el = entry.find(f"{{{ns_atom}}}link[@rel='alternate']") or entry.find(f"{{{ns_atom}}}link")
        link = link_el.get("href", "") if link_el is not None else ""

        pub_raw = ""
        for tag in ("published", "updated"):
            el = entry.find(f"{{{ns_atom}}}{tag}")
            if el is not None and el.text:
                pub_raw = el.text
                break
        pub_date = _parse_date(pub_raw)
        if pub_date and pub_date < cutoff:
            continue

        summary_el = (entry.find(f"{{{ns_atom}}}content") or entry.find(f"{{{ns_atom}}}summary"))
        raw_summary = (summary_el.text or "") if summary_el is not None else ""
        summary = _strip_html(raw_summary)[:600]

        if not title or not link:
            continue
        if feed_info["name"] not in AI_SPECIFIC_SOURCES:
            if not is_ai_related(title, summary):
                continue
        articles.append({
            "source": feed_info["name"],
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

        # ET.fromstring can raise on bad XML — wrap it
        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as e:
            print(f"  [WARN] XML parse error for {feed_info['name']}: {e}")
            return []

        tag = root.tag.lower()
        if "rss" in tag or "rdf" in tag or root.tag == "rss":
            return _parse_rss_feed(root, feed_info, cutoff)
        elif "feed" in root.tag:  # Atom
            return _parse_atom_feed(root, feed_info, cutoff)
        else:
            # Unknown format — try both
            arts = _parse_rss_feed(root, feed_info, cutoff)
            if not arts:
                arts = _parse_atom_feed(root, feed_info, cutoff)
            return arts
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
        time.sleep(0.3)

    seen_titles = set()
    unique_articles = []
    for a in all_articles:
        key = a["title"].lower()[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_articles.append(a)

    print(f"Found {len(unique_articles)} unique AI articles.")
    return unique_articles
