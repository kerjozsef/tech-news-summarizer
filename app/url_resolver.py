"""Resolve feed link to the canonical article URL (e.g. Reddit post -> linked article)."""
import html as html_module
import re
from typing import Any, List, Optional


def get_external_link_from_entry_links(links: Any, exclude_domain: str = "reddit.com") -> Optional[str]:
    """
    From a feed entry's links list (e.g. entry.links from feedparser), return the first
    https URL that does not contain exclude_domain. Use when the feed exposes the
    original article as a separate link.
    """
    if not links:
        return None
    exclude = exclude_domain.lower()
    try:
        for link in links:
            href = link.get("href", "") if isinstance(link, dict) else getattr(link, "href", "")
            if not href or not isinstance(href, str):
                continue
            href = href.strip()
            if href.startswith("http") and exclude not in href.lower():
                if not href.rstrip("/").endswith(".rss"):
                    return href
    except (TypeError, AttributeError):
        pass
    return None


def extract_first_external_link(html: str, exclude_domain: str = "reddit.com") -> Optional[str]:
    """
    From HTML (e.g. feed summary), return the first https URL that does not
    contain exclude_domain. Prefers href attributes, then plain URLs.
    Decodes HTML entities so encoded content doesn't hide URLs.
    """
    if not html or not isinstance(html, str):
        return None
    try:
        html = html_module.unescape(html)
    except Exception:
        pass
    exclude = exclude_domain.lower()
    # Prefer href="https://..." (double or single quoted)
    for m in re.finditer(r'href\s*=\s*["\'](https://[^"\']+)["\']', html, re.I):
        url = m.group(1).strip()
        if exclude not in url.lower() and not url.rstrip("/").endswith(".rss"):
            return url
    # Plain https URLs (skip common false positives like reddit domains)
    for m in re.finditer(r'https://(?:[^\s"\'<>)\]]+)', html):
        url = m.group(0).strip()
        if exclude not in url.lower():
            return url
    return None
