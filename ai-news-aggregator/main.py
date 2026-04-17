#!/usr/bin/env python3
"""
AI News Aggregator — Daily Digest
Fetches AI news, summarizes with Claude, and emails a beautiful digest.
"""
import sys
import json
import argparse
from datetime import datetime

from news_fetcher import fetch_all_news
from summarizer import summarize_news
from email_sender import send_digest_email


def main():
    parser = argparse.ArgumentParser(description="AI Daily News Digest")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch and summarize but do not send email")
    parser.add_argument("--save-digest", metavar="FILE",
                        help="Save the digest JSON to a file")
    parser.add_argument("--lookback-hours", type=int, default=24,
                        help="How many hours back to fetch news (default: 24)")
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

    # Step 3: Optionally save digest
    if args.save_digest:
        with open(args.save_digest, "w") as f:
            json.dump(digest, f, indent=2)
        print(f"Digest saved to {args.save_digest}")

    # Step 4: Send email
    if args.dry_run:
        print("\n[DRY RUN] Email not sent. Digest summary:")
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

    try:
        send_digest_email(digest)
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        sys.exit(1)

    print("\nAI Daily Digest complete!")


if __name__ == "__main__":
    main()
