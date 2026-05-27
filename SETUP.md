# AI News Aggregator — Setup Guide

This project fetches AI news daily, summarizes it with an LLM, and emails you a digest every morning at **7:00 AM UTC (12:30 PM IST)**.

---

## ⚡ One-time Setup: GitHub Secrets

Go to your repository → **Settings → Secrets and variables → Actions → New repository secret** and add **three secrets**:

| Secret Name      | Value                                                                 |
|------------------|-----------------------------------------------------------------------|
| `GROQ_API_KEY`   | Your Groq API key from [console.groq.com](https://console.groq.com) (free tier works) |
| `EMAIL_FROM`     | The Gmail address that *sends* the digest (e.g. `yourname@gmail.com`) |
| `EMAIL_PASSWORD` | A **Gmail App Password** — NOT your Gmail login password (see below) |

> **`EMAIL_TO` is already hardcoded** to `bishambarsingh333@gmail.com` in the workflow.  
> Change it there if you ever want to send to a different address.

---

## 🔑 Creating a Gmail App Password

Gmail requires an App Password (not your login password) for SMTP:

1. Enable **2-Step Verification** on your Google account  
   → [myaccount.google.com/security](https://myaccount.google.com/security)

2. Go to **App Passwords**  
   → [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

3. Select **Mail** + **Other (Custom name)** → type `AI News Bot` → click **Generate**

4. Copy the 16-character password and save it as the `EMAIL_PASSWORD` secret.

---

## 🚀 Running Manually

Trigger any time via **Actions → Daily AI News Digest → Run workflow**.

Options:
- `dry_run = true` → fetch + summarize but skip writing the file and sending email
- `lookback_hours` → how far back to look for news (default: 24)

---

## 📁 Project Structure

```
AI-Projects/
├── .github/workflows/daily-ai-news.yml   ← GitHub Actions (runs daily at 7 AM UTC)
├── ai-news-aggregator/
│   ├── main.py           ← entry point
│   ├── news_fetcher.py   ← RSS scraper (15 AI sources)
│   ├── summarizer.py     ← Groq LLM categorizer & summarizer
│   ├── email_sender.py   ← Gmail SMTP sender (HTML + plain text)
│   ├── digest_store.py   ← saves JSON digest, prunes files > 7 days
│   └── requirements.txt
└── digests/              ← daily JSON digests committed by the bot
```

---

## 📧 What the Email Looks Like

- **Subject**: `AI Daily Digest — 2026-05-27: <top headline>`
- **Format**: Styled HTML email (with plain-text fallback)
- **Sections**: Top Story · New Models · Research · Features · Industry · Policy
- **Sources**: TechCrunch, VentureBeat, MIT Tech Review, The Verge, Wired, Ars Technica, OpenAI Blog, Google DeepMind, Hugging Face, and more (15 feeds total)
