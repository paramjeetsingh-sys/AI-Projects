import json
import os
from typing import Dict
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SUMMARY_HEADERS = [
    "Date", "Headline", "TL;DR", "Total Articles",
    "Top Story", "Top Story Source", "Top Story Link",
    "New Models", "Research", "Features & Updates", "Industry & Business", "Policy & Society",
]

ARTICLE_HEADERS = [
    "Date", "Category", "Title", "Source", "Link", "Summary", "Why It Matters",
]

CATEGORY_LABELS = {
    "new_models": "New Models & Launches",
    "research": "Research & Breakthroughs",
    "features_updates": "Features & Updates",
    "industry_business": "Industry & Business",
    "policy_society": "Policy & Society",
}


def _get_client(creds_json: str) -> gspread.Client:
    info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.Client(auth=creds)


def _get_or_create_worksheet(spreadsheet: gspread.Spreadsheet, title: str) -> gspread.Worksheet:
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=1000, cols=20)


def _ensure_headers(ws: gspread.Worksheet, headers: list) -> None:
    if not ws.row_values(1):
        ws.update("A1", [headers])


def write_digest_to_sheet(digest: Dict) -> bool:
    creds_json = os.environ.get("GOOGLE_CREDENTIALS") or ""
    sheet_id = os.environ.get("GOOGLE_SHEET_ID") or ""

    if not creds_json or not sheet_id:
        print("[INFO] GOOGLE_CREDENTIALS or GOOGLE_SHEET_ID not set; skipping Sheets write.")
        return False

    print("Writing digest to Google Sheets...")

    try:
        client = _get_client(creds_json)
        spreadsheet = client.open_by_key(sheet_id)

        date = digest.get("date", datetime.now().strftime("%Y-%m-%d"))
        cats = digest.get("categories", {})
        top = digest.get("top_story") or {}

        # "Daily Digests" tab — one summary row per day
        summary_ws = _get_or_create_worksheet(spreadsheet, "Daily Digests")
        _ensure_headers(summary_ws, SUMMARY_HEADERS)
        summary_ws.append_row([
            date,
            digest.get("headline", ""),
            digest.get("tldr", ""),
            digest.get("total_articles", 0),
            top.get("title", ""),
            top.get("source", ""),
            top.get("link", ""),
            len(cats.get("new_models", [])),
            len(cats.get("research", [])),
            len(cats.get("features_updates", [])),
            len(cats.get("industry_business", [])),
            len(cats.get("policy_society", [])),
        ], value_input_option="USER_ENTERED")

        # "Articles" tab — one row per article across all categories
        articles_ws = _get_or_create_worksheet(spreadsheet, "Articles")
        _ensure_headers(articles_ws, ARTICLE_HEADERS)
        rows = [
            [
                date,
                label,
                a.get("title", ""),
                a.get("source", ""),
                a.get("link", ""),
                a.get("summary", ""),
                a.get("why_it_matters", ""),
            ]
            for cat_key, label in CATEGORY_LABELS.items()
            for a in cats.get(cat_key, [])
        ]
        if rows:
            articles_ws.append_rows(rows, value_input_option="USER_ENTERED")

        print(f"Google Sheets updated: 1 summary row + {len(rows)} article rows.")
        return True

    except Exception as e:
        print(f"[WARN] Failed to write to Google Sheets: {e}")
        return False
