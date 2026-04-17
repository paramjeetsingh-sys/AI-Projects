import feedparser
import requests
from datetime import datetime, timezone, timedelta
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


def is_ai_related(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def parse_published_date(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def fetch_feed(feed_info: Dict, cutoff: datetime) -> List[Dict]:
    articles = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AINewsBot/1.0)"}
        resp = requests.get(feed_info["url"], headers=headers, timeout=15)
        feed = feedparser.parse(resp.content)

        for entry in feed.entries:
            pub_date = parse_published_date(entry)

            # Include articles from today (or undated ones as fallback)
            if pub_date and pub_date < cutoff:
                continue

            title = getattr(entry, "title", "").strip()
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            # Strip HTML tags from summary
            import re
            summary = re.sub(r"<[^>]+>", " ", summary).strip()
            summary = re.sub(r"\s+", " ", summary)[:600]

            link = getattr(entry, "link", "")

            if not title or not link:
                continue

            # For non-AI-specific feeds, filter by keyword
            if feed_info["name"] not in ("OpenAI Blog", "Google DeepMind", "Hugging Face Blog", "NVIDIA Blog", "Microsoft AI Blog"):
                if not is_ai_related(title, summary):
                    continue

            articles.append({
                "source": feed_info["name"],
                "title": title,
                "summary": summary,
                "link": link,
                "published": pub_date.strftime("%Y-%m-%d %H:%M UTC") if pub_date else "Today",
            })
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
        time.sleep(0.3)  # polite delay

    # Deduplicate by title similarity
    seen_titles = set()
    unique_articles = []
    for a in all_articles:
        key = a["title"].lower()[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_articles.append(a)

    print(f"Found {len(unique_articles)} unique AI articles.")
    return unique_articles
