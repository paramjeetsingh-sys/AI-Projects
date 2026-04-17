# AI News Aggregator

Fetches daily AI news from 15+ sources, summarizes with Claude, and emails a beautiful HTML digest.

## Setup

### 1. GitHub Secrets Required

Go to your repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `SMTP_HOST` | `smtp.gmail.com` (for Gmail) |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your sender Gmail address |
| `SMTP_PASSWORD` | Gmail App Password (see below) |

### 2. Gmail App Password

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Go to App Passwords → Select app: Mail → Generate
4. Use the 16-character password as `SMTP_PASSWORD`

## Schedule

Runs automatically at **7:00 AM UTC (12:30 PM IST)** every day.

To trigger manually: Actions → Daily AI News Digest → Run workflow

## Local Run

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY=your_key
export SMTP_USER=sender@gmail.com
export SMTP_PASSWORD=your_app_password

# Dry run (no email)
python main.py --dry-run

# Send email
python main.py

# Fetch last 48 hours
python main.py --lookback-hours 48
```

## News Sources

TechCrunch AI · VentureBeat AI · MIT Technology Review · The Verge AI · Wired AI ·
Ars Technica · OpenAI Blog · Google DeepMind · Hugging Face · AI News · Analytics Vidhya ·
Towards Data Science · InfoQ · NVIDIA Blog · Microsoft AI Blog
