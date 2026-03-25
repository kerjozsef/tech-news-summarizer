"""Send the daily digest email via SMTP."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    EMAIL_FROM,
    EMAIL_TO,
)


def send_digest_email(summary: str, subject_prefix: str = "Tech News Digest") -> None:
    """
    Send the summarized digest to EMAIL_TO using SMTP.
    Uses TLS on the given port (typically 587).
    """
    if not EMAIL_TO:
        raise ValueError("EMAIL_TO is not set in environment")
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be set for sending email")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"{subject_prefix} – {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM or SMTP_USER
    msg["To"] = EMAIL_TO

    plain = summary
    msg.attach(MIMEText(plain, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM or SMTP_USER, [EMAIL_TO], msg.as_string())
