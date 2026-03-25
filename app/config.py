"""Configuration loaded from environment variables and/or Docker secrets."""
import os
from pathlib import Path


def _read_secret(env_name: str) -> str:
    """
    Read a secret from Docker secrets if available.
    Looks for /run/secrets/<ENV_NAME> and /run/secrets/<env_name.lower()>.
    Returns empty string if not found or on error.
    """
    base = Path("/run/secrets")
    for candidate in (env_name, env_name.lower()):
        try:
            secret_path = base / candidate
            if secret_path.is_file():
                return secret_path.read_text(encoding="utf-8").strip()
        except Exception:
            continue
    return ""

# OpenAI (for summarization)
OPENAI_API_KEY = _read_secret("OPENAI_API_KEY") or os.getenv("openai_api_key") or os.getenv("API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Email (SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
except ValueError:
    SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = _read_secret("SMTP_PASSWORD") or os.getenv("smtp_password", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.getenv("EMAIL_TO", "")

# Optional: max articles to fetch and include in summary (default 3 for ntfy Actions)
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "3"))

# ntfy (self-hosted push) - optional; if set, digest is also sent to ntfy
NTFY_BASE_URL = os.getenv("NTFY_BASE_URL", "").rstrip("/")  # e.g. https://ntfy.example.com
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "tech-news-digest")
NTFY_TOKEN = _read_secret("NTFY_TOKEN") or os.getenv("ntfy_token", "")  # access token for Authorization: Bearer
