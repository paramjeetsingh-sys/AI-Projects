# AI News Aggregator

Fetches daily AI news from 15+ sources, summarizes with Llama 3.3 70B via Groq, and emails a beautiful HTML digest.

## Setup

### 1. GitHub Secrets Required

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Required | Value |
|--------|----------|-------|
| `GROQ_API_KEY` | Yes | Your Groq API key (free at [console.groq.com](https://console.groq.com)) |
| `EMAIL_FROM` | Optional | Sender email address (e.g. `you@gmail.com`) |
| `EMAIL_PASSWORD` | Optional | Gmail App Password (see below) |
| `EMAIL_TO` | Optional | Recipient email(s), comma-separated |

Email secrets are optional — if omitted, the digest is still saved as a JSON file in `digests/` and committed to the repo. You can browse digests directly on GitHub.

### 2. Gmail App Password (for email delivery)

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Go to **App Passwords** → Select app: Mail → Generate
4. Use the 16-character password as `EMAIL_PASSWORD`

### 3. Groq API Key (free)

1. Sign up at [console.groq.com](https://console.groq.com)
2. Go to **API Keys** → Create new key
3. Add it as the `GROQ_API_KEY` secret in your repo

## Schedule

Runs automatically at **7:00 AM UTC (12:30 PM IST)** every day.

To trigger manually: **Actions → Daily AI News Digest → Run workflow**

## Local Run

```bash
cd ai-news-aggregator
pip install -r requirements.txt

# Copy and fill in your credentials
cp .env.example .env
# Edit .env and set GROQ_API_KEY (and optional email vars)

# Dry run — fetches & summarizes but does NOT write the digest file
python main.py --dry-run

# Full run — writes digest to digests/<date>.json, sends email if configured
python main.py

# Fetch last 48 hours of news
python main.py --lookback-hours 48

# Skip email even if credentials are configured
python main.py --no-email
```

## Output

Each run writes a JSON file to `digests/YYYY-MM-DD.json` and keeps only the last 7 days.
The GitHub Actions workflow commits this file automatically so you can browse past digests on GitHub.

## News Sources

TechCrunch AI · VentureBeat AI · MIT Technology Review · The Verge AI · Wired AI ·
Ars Technica · OpenAI Blog · Google DeepMind · Hugging Face · AI News · Analytics Vidhya ·
Towards Data Science · InfoQ · NVIDIA Blog · Microsoft AI Blog
