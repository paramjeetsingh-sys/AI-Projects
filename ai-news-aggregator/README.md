# AI News Aggregator

Fetches daily AI news from 15+ sources, summarizes with Groq (LLaMA 3.3 70B), and emails a beautiful HTML digest.

## Setup

### 1. GitHub Secrets Required

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
|--------|-------|
| `GROQ_API_KEY` | Your Groq API key (free at console.groq.com) |
| `EMAIL_FROM` | Sender Gmail address (e.g. `you@gmail.com`) |
| `EMAIL_PASSWORD` | Gmail App Password (16-char, see below) |
| `EMAIL_TO` | Recipient address(es), comma-separated |
| `SMTP_HOST` | `smtp.gmail.com` *(optional, this is the default)* |
| `SMTP_PORT` | `587` *(optional, this is the default)* |

### 2. Gmail App Password

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Go to **App Passwords** → Select app: Mail → Generate
4. Use the 16-character password as `EMAIL_PASSWORD`

## Schedule

Runs automatically at **7:00 AM UTC (12:30 PM IST)** every day.

To trigger manually: **Actions → Daily AI News Digest → Run workflow**

## Local Run

```bash
pip install -r requirements.txt

export GROQ_API_KEY=your_key
export EMAIL_FROM=sender@gmail.com
export EMAIL_PASSWORD=your_app_password
export EMAIL_TO=recipient@gmail.com

# Dry run (no email, no file written)
python main.py --dry-run

# Send email
python main.py

# Fetch last 48 hours
python main.py --lookback-hours 48

# Skip email (just save the digest file)
python main.py --no-email
```

## News Sources

TechCrunch AI · VentureBeat AI · MIT Technology Review · The Verge AI · Wired AI ·
Ars Technica · OpenAI Blog · Google DeepMind · Hugging Face · AI News · Analytics Vidhya ·
Towards Data Science · InfoQ · NVIDIA Blog · Microsoft AI Blog
