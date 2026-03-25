"""Fetch article HTML and extract main text for summarization."""
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

# Max chars of article text to send to the summarizer
ARTICLE_TEXT_MAX = 4000

# Request timeout and simple browser User-Agent
FETCH_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (compatible; TechNewsDigest/1.0)"


def fetch_article_text(url: str) -> str:
    """
    Fetch URL and return main body text (strip HTML, scripts, etc.).
    Returns up to ARTICLE_TEXT_MAX characters; empty string on failure.
    Skips Reddit URLs so we never summarize the Reddit page instead of the linked article.
    """
    if not url or not url.strip().startswith("http"):
        return ""
    if "reddit.com" in url.lower():
        return ""
    try:
        r = requests.get(
            url,
            timeout=FETCH_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        r.raise_for_status()
        html = r.text
    except Exception:
        return ""
    return _extract_text(html)


def _extract_text(html: str) -> str:
    """Extract readable text from HTML."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
            tag.decompose()
        body = soup.find("body") or soup
        text = body.get_text(separator=" ", strip=True)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        return text[:ARTICLE_TEXT_MAX] if text else ""
    except Exception:
        return ""
