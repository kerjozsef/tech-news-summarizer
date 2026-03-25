"""Fetch recent tech news from RSS feeds."""
import re
import feedparser
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from config import MAX_ARTICLES
from url_resolver import extract_first_external_link, get_external_link_from_entry_links


@dataclass
class NewsItem:
    """Single news article."""
    title: str
    link: str
    source: str
    published: Optional[datetime]
    summary: str


# Tech-focused RSS feeds (no duplicates, tech/gadgets/programming)
TECH_FEEDS = [
    "https://news.ycombinator.com/rss",
    "https://techcrunch.com/tag/feed/",
    "https://feeds.feedburner.com/techcrunch",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.reddit.com/r/technology/.rss",
    "https://www.reddit.com/r/programming/.rss",
]

# Keywords to keep only tech-related articles (title or summary must match at least one)
TECH_KEYWORDS = [
    "tech", "software", "hardware", "computer", "programming", "code", "developer",
    "AI", "artificial intelligence", "machine learning", "algorithm", "data",
    "startup", "app", "application", "internet", "digital", "cloud", "cyber",
    "chip", "CPU", "GPU", "smartphone", "gadget", "robot", "automation",
    "open source", "open-source", "API", "security", "hack", "crypto", "blockchain",
    "Google", "Apple", "Microsoft", "Amazon", "Meta", "Facebook", "Tesla",
    "iPhone", "Android", "Windows", "Linux", "Python", "JavaScript", "coding",
]


def _is_tech_related(item: "NewsItem") -> bool:
    """True if the article appears tech-related (title or summary matches TECH_KEYWORDS)."""
    text = f"{item.title} {item.summary}".lower()
    return any(kw.lower() in text for kw in TECH_KEYWORDS)


def _parse_date(entry) -> Optional[datetime]:
    """Parse published/updated date from feed entry."""
    for key in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, key, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    return None


def _get_summary(entry) -> str:
    """Get summary or description from entry."""
    raw = getattr(entry, "summary", None) or getattr(entry, "description", None)
    if not raw or not hasattr(raw, "strip"):
        return ""
    text = re.sub(r"<[^>]+>", "", raw).strip()
    if len(text) <= 500:
        return text
    return text[:500] + "..."


def fetch_tech_news(max_articles: int = MAX_ARTICLES) -> List[NewsItem]:
    """
    Fetch and normalize tech news from all configured feeds.
    Returns a list of NewsItem, sorted by date (newest first), limited to max_articles.
    """
    items: List[NewsItem] = []
    seen_links = set()

    for feed_url in TECH_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source = feed.feed.get("title", feed_url)
            for entry in feed.entries:
                link = getattr(entry, "link", "").strip()
                if not link or link in seen_links:
                    continue
                # If this is a Reddit (or similar) link, use the original article URL when available
                if "reddit.com" in link.lower():
                    canonical = None
                    raw_html = getattr(entry, "summary", None) or getattr(entry, "description", None)
                    canonical = extract_first_external_link(raw_html or "")
                    if not canonical:
                        canonical = get_external_link_from_entry_links(getattr(entry, "links", []))
                    if canonical:
                        link = canonical
                seen_links.add(link)
                title = getattr(entry, "title", "").strip() or "(No title)"
                items.append(
                    NewsItem(
                        title=title,
                        link=link,
                        source=source,
                        published=_parse_date(entry),
                        summary=_get_summary(entry),
                    )
                )
        except Exception as e:
            print(f"Warning: failed to parse feed {feed_url}: {e}")
            continue

    # Sort by date (newest first), put None dates last
    items.sort(key=lambda x: (x.published or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    # Keep only tech-related articles, then limit count
    items = [i for i in items if _is_tech_related(i)]
    return items[:max_articles]


if __name__ == "__main__":
    for item in fetch_tech_news(max_articles=5):
        print(f"[{item.source}] {item.title}")
        print(f"  {item.link}\n")
