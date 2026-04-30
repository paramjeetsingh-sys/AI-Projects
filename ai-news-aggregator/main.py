#!/usr/bin/env python3
"""
AI News Aggregator — Daily Digest
Fetches AI news, summarizes with Groq, and saves a daily JSON digest to the repo.
"""
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader — no external deps required."""
    if not path.exists():
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv(Path(__file__).parent / ".env")

from news_fetcher import fetch_all_news
from summarizer import summarize_news
from digest_store import save_daily_digest, cleanup_old_digests
from email_sender import send_digest_email


def main():
    parser = argparse.ArgumentParser(description="AI Daily News Digest")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch and summarize but do not write the digest file")
    parser.add_argument("--lookback-hours", type=int, default=24,
                        help="How many hours back to fetch news (default: 24)")
    parser.add_argument("--no-email", action="store_true",
                        help="Skip sending the email even if credentials are configured")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  AI Daily Digest — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    articles = fetch_all_news(lookback_hours=args.lookback_hours)

    if not articles:
        print("[WARN] No articles found. Check network or RSS feed URLs.")

    digest = summarize_news(articles)

    if args.dry_run:
        print("\n[DRY RUN] Digest not written. Summary:")
        print(f"  Date: {digest.get('date')}")
        print(f"  Total articles: {digest.get('total_articles')}")
        print(f"  Headline: {digest.get('headline')}")
        print(f"  TL;DR: {digest.get('tldr')}")
        cats = digest.get("categories", {})
        for cat, items in cats.items():
            if items:
                print(f"  {cat}: {len(items)} articles")
        print("\nDry run complete.")
        return

    save_daily_digest(digest)
    removed = cleanup_old_digests(keep_days=7)
    if removed:
        print(f"Pruned {len(removed)} old digest(s): {', '.join(removed)}")

    if not args.no_email:
        send_digest_email(digest)

    print("\nAI Daily Digest complete!")


if __name__ == "__main__":
    main()
