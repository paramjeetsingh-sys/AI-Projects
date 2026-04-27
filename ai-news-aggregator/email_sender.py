import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict

from email_template import build_html_email, build_plain_text_email


def send_digest_email(digest: Dict) -> bool:
    # Use `or` so that an empty-string env var (e.g. unset GitHub secret) falls back to the default
    smtp_host = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
    smtp_port = int(os.environ.get("SMTP_PORT") or "587")
    smtp_user = os.environ.get("SMTP_USER") or ""
    smtp_password = os.environ.get("SMTP_PASSWORD") or ""
    recipient = os.environ.get("RECIPIENT_EMAIL", "paramjeet.singh@classplus.co")

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD environment variables are required.")

    date_str = digest.get("date", datetime.now().strftime("%Y-%m-%d"))
    subject = f"🤖 AI Daily Digest — {date_str} | {digest.get('total_articles', 0)} Stories"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI News Aggregator <{smtp_user}>"
    msg["To"] = recipient

    plain_text = build_plain_text_email(digest)
    html_content = build_html_email(digest)

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    print(f"Sending digest email to {recipient}...")
    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient, msg.as_string())

    print(f"Email sent successfully to {recipient}!")
    return True
