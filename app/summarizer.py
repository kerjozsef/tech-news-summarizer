"""Summarize tech news using OpenAI."""
from typing import List

from news_fetcher import NewsItem
from config import OPENAI_API_KEY, OPENAI_MODEL


def build_news_text(items: List[NewsItem]) -> str:
    """Turn news items into a single text block for the model."""
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. [{item.source}] {item.title}")
        lines.append(f"   URL: {item.link}")
        if item.summary:
            snippet = item.summary[:300] + "..." if len(item.summary) > 300 else item.summary
            lines.append(f"   Summary: {snippet}")
        lines.append("")
    return "\n".join(lines)


def summarize_with_openai(items: List[NewsItem]) -> str:
    """
    Call OpenAI to summarize the given news items.
    Returns a string suitable for the daily email body.
    """
    if not OPENAI_API_KEY:
        return _fallback_summary(items)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        return _fallback_summary(items)

    news_text = build_news_text(items)
    num = len(items)
    prompt = f"""You are a tech news editor. Below are {num} tech headlines. Your task is to cover every single one.

For EACH of the {num} articles, output exactly this format (no markdown, plain text):

• [Article title or a short headline]
  [One or two sentences summarizing the story and why it matters.]
  Link: [paste the full URL exactly as given below]

Do not skip any article. Do not merge multiple articles into one. Keep each summary to 1–2 sentences. Always include the "Link: [URL]" line for every article. Use the exact URLs from the list below.

HEADLINES AND URLs TO COVER:
{news_text}
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=min(4096, 200 * num + 500),  # enough for all articles + intro
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        return _fallback_summary(items, error=str(e))


def summarize_article_brief(title: str, text: str) -> str:
    """
    Summarize a single article in 2-3 sentences for ntfy.
    Uses the original article text (e.g. from the canonical URL, not Reddit).
    Returns empty string if no API key or text is empty.
    """
    if not OPENAI_API_KEY or not (text or "").strip():
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        return ""
    content = (text or "").strip()[:3500]
    prompt = f"""Summarize this article in 2-3 short sentences. Focus on what it says and why it matters. Plain text only, no markdown.

Title: {title}

Article excerpt:
{content}
"""
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        out = (response.choices[0].message.content or "").strip()
        return out if out else ""
    except Exception:
        return ""


def _fallback_summary(items: List[NewsItem], error: str = "") -> str:
    """When API is missing or fails, return a simple bullet list."""
    intro = "Summary unavailable (missing OPENAI_API_KEY or API error). Here are the top headlines:\n\n"
    if error:
        intro = f"Summary unavailable: {error}\n\nTop headlines:\n\n"
    body = "\n".join(f"• {item.title}\n  {item.link}" for item in items)
    return intro + body
