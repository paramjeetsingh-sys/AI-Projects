#!/usr/bin/env python3
"""
AI News Aggregator — Daily Digest
Fetches AI news, summarizes with Claude, and saves a daily JSON digest to the repo.
"""
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Load .env if present (optional; no error if file is missing)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=False)
except ImportError:
    pass

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

    # Step 1: Fetch news
    articles = fetch_all_news(lookback_hours=args.lookback_hours)

    if not articles:
        print("[WARN] No articles found. Check network or RSS feed URLs.")

    # Step 2: Summarize with Claude
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

    # Step 3: Save today's file and prune files older than 7 days
    save_daily_digest(digest)
    removed = cleanup_old_digests(keep_days=7)
    if removed:
        print(f"Pruned {len(removed)} old digest(s): {', '.join(removed)}")

    # Step 4: Send email digest
    if not args.no_email:
        send_digest_email(digest)

    print("\nAI Daily Digest complete!")


if __name__ == "__main__":
    main()
