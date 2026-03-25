"""Send the daily digest to a self-hosted ntfy server (push notifications)."""
from datetime import datetime, timezone
from typing import List, Optional

import requests

from config import NTFY_BASE_URL, NTFY_TOPIC, NTFY_TOKEN
from news_fetcher import NewsItem

# ntfy allows up to 3 actions per notification
NTFY_ACTIONS_MAX = 3

# One-line summary max length (from RSS snippet)
SUMMARY_LINE_MAX = 120


def _looks_like_reddit_metadata(text: str) -> bool:
    """True if text is Reddit post metadata (submitted by, /u/, [link], [comments]), not article content."""
    if not text or len(text.strip()) < 10:
        return False
    t = text.lower()
    return (
        "submitted by" in t or "/u/" in t or "[link]" in t or "[comments]" in t
        or "&#32;" in text or " submitted " in t
    )


def _one_line_summary(summary: str) -> str:
    """First sentence or first SUMMARY_LINE_MAX chars, single line. Returns '' if Reddit metadata."""
    if not summary or not summary.strip():
        return ""
    if _looks_like_reddit_metadata(summary):
        return ""
    text = summary.strip().replace("\n", " ").replace("\r", " ")
    # First sentence
    for end in ".!?":
        i = text.find(end)
        if i != -1:
            line = text[: i + 1].strip()
            return line if len(line) <= SUMMARY_LINE_MAX else line[: SUMMARY_LINE_MAX - 3] + "..."
    return text[:SUMMARY_LINE_MAX] + ("..." if len(text) > SUMMARY_LINE_MAX else "")


def send_digest_to_ntfy(
    items: List[NewsItem],
    title_prefix: str = "Tech News Digest",
    summaries: Optional[List[str]] = None,
) -> None:
    """
    POST a single notification: body = headline + 2-3 sentence summary per article
    (or RSS snippet if summaries not provided); buttons = "Read article 1/2/3".
    summaries: optional list of brief AI summaries from the original article (one per item).
    """
    if not NTFY_BASE_URL:
        raise ValueError("NTFY_BASE_URL is not set in environment")
    if not NTFY_TOPIC:
        raise ValueError("NTFY_TOPIC is not set in environment")

    url = f"{NTFY_BASE_URL}/{NTFY_TOPIC}"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"{title_prefix} - {today}"

    action_items = items[:NTFY_ACTIONS_MAX]

    # Body: intro, then for each article — separator, headline (bold+italic), blank line, summary
    lines = ["Tap a button below to open the article.", ""]
    for i, item in enumerate(action_items):
        lines.append(f"——— {i + 1} ———")
        lines.append(f"***{item.title}***")
        lines.append("")
        if summaries and i < len(summaries) and (summaries[i] or "").strip():
            lines.append(summaries[i].strip())
        else:
            snippet = _one_line_summary(item.summary)
            if snippet:
                lines.append(snippet)
            elif _looks_like_reddit_metadata(item.summary or ""):
                lines.append("Summary unavailable (link post).")
        lines.append("")
    body = "\n".join(lines).strip()

    # Short same-length labels so they stay on one line when buttons are narrow
    button_labels = [f"Article {i}" for i in range(1, len(action_items) + 1)]

    headers = {"Title": title, "Markdown": "yes"}
    action_parts = []
    for item, label in zip(action_items, button_labels):
        action_parts.append(f"view, {label}, {item.link}")
    if action_parts:
        headers["Actions"] = "; ".join(action_parts)
    if NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {NTFY_TOKEN}"

    response = requests.post(
        url,
        data=body.encode("utf-8"),
        headers=headers,
        timeout=30,
    )
    if not response.ok:
        err = response.text or response.reason
        raise RuntimeError(f"{response.status_code} {response.reason}: {err}")


def ntfy_configured() -> bool:
    """True if ntfy is configured (base URL and topic; token optional for public topics)."""
    return bool(NTFY_BASE_URL and NTFY_TOPIC)
