#!/usr/bin/env python3
"""
AI Evals Platform — evaluate AI conversations from Redash CSV data.

Usage:
  # From Redash query:
  python main.py --query-id 42

  # From local CSV file:
  python main.py --csv-file path/to/chats.csv

  # Limit sessions and customize output:
  python main.py --csv-file chats.csv --limit 20 --output-dir ./reports

  # Custom column mapping:
  python main.py --csv-file chats.csv --col-user uid --col-session sid --col-role from --col-content text
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from config import Config, ColumnMapping
from redash_client import RedashClient
from data_processor import process_csv_rows
from eval_runner import EvalRunner
from report_generator import generate_html_report, generate_json_report


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Evals Platform — evaluate AI conversations from Redash"
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--query-id", type=int, help="Redash query ID to fetch")
    source.add_argument("--csv-file", type=str, help="Local CSV file path")

    parser.add_argument("--limit", type=int, default=None, help="Max sessions to evaluate")
    parser.add_argument("--output-dir", default="eval_reports", help="Output directory")
    parser.add_argument("--formats", default="html,json", help="Report formats (html,json)")
    parser.add_argument("--max-messages", type=int, default=50, help="Max messages per session")

    # Column mapping overrides
    parser.add_argument("--col-user", default="user_id", help="Column name for user ID")
    parser.add_argument("--col-session", default="session_id", help="Column name for session ID")
    parser.add_argument("--col-timestamp", default="timestamp", help="Column name for timestamp")
    parser.add_argument("--col-role", default="role", help="Column name for message role")
    parser.add_argument("--col-content", default="message", help="Column name for message content")
    parser.add_argument("--user-role-value", default="user", help="Value indicating user role")
    parser.add_argument("--assistant-role-value", default="assistant", help="Value indicating AI role")

    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("AI Evals Platform")
    print("=" * 60)

    config = Config.from_env()
    config.output_dir = args.output_dir
    config.max_messages_per_session = args.max_messages
    config.column_mapping = ColumnMapping(
        user_id=args.col_user,
        session_id=args.col_session,
        timestamp=args.col_timestamp,
        role=args.col_role,
        content=args.col_content,
        user_role_value=args.user_role_value,
        assistant_role_value=args.assistant_role_value,
    )

    # Step 1: Fetch data
    print("\n[1/4] Fetching conversation data...")
    client = RedashClient(config)

    if args.query_id:
        if not config.redash_url or not config.redash_api_key:
            print("ERROR: REDASH_URL and REDASH_API_KEY must be set for Redash queries.", file=sys.stderr)
            sys.exit(1)
        rows = client.fetch_query_csv(args.query_id)
        print(f"  Fetched {len(rows)} rows from Redash query {args.query_id}")
    else:
        rows = client.fetch_from_csv_file(args.csv_file)
        print(f"  Loaded {len(rows)} rows from {args.csv_file}")

    if not rows:
        print("ERROR: No data found.", file=sys.stderr)
        sys.exit(1)

    # Step 2: Process data
    print("\n[2/4] Processing conversation data...")
    chat_data = process_csv_rows(rows, config)
    print(f"  Found {chat_data.total_sessions} sessions across {len(chat_data.sessions_by_user)} users")

    if chat_data.total_sessions == 0:
        print("ERROR: No sessions found. Check your column mapping.", file=sys.stderr)
        sys.exit(1)

    # Step 3: Run evaluations
    print(f"\n[3/4] Running evaluations (limit={args.limit or 'all'})...")
    print(f"  Model: {config.model}")
    print(f"  Evaluating: Accuracy | Engagement | Topic Shifting\n")

    runner = EvalRunner(config)
    results = runner.run_all(chat_data, limit=args.limit, verbose=True)

    # Step 4: Generate reports
    print(f"\n[4/4] Generating reports...")
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    formats = [f.strip() for f in args.formats.split(",")]
    generated = []

    if "html" in formats:
        path = os.path.join(args.output_dir, f"eval_report_{timestamp}.html")
        generate_html_report(results, path)
        generated.append(path)
        print(f"  HTML report: {path}")

    if "json" in formats:
        path = os.path.join(args.output_dir, f"eval_report_{timestamp}.json")
        generate_json_report(results, path)
        generated.append(path)
        print(f"  JSON report: {path}")

    # Summary
    valid = [r for r in results if r.overall_score > 0]
    if valid:
        avg = sum(r.overall_score for r in valid) / len(valid)
        print(f"\n{'=' * 60}")
        print(f"SUMMARY: {len(results)} sessions evaluated")
        print(f"  Average overall score: {avg:.1f}/10")
        errors = [r for r in results if r.error]
        if errors:
            print(f"  Sessions with errors: {len(errors)}")
        print("=" * 60)


if __name__ == "__main__":
    main()
