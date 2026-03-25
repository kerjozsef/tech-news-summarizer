#!/usr/bin/env python3
"""
Tech News Summarizer – fetch tech news, summarize with AI, send via email and/or ntfy.

Run once (e.g. via cron):
  python main.py --email              # send by email only
  python main.py --ntfy               # send to ntfy only
  python main.py --email --ntfy       # send to both
  python main.py --dry-run            # no sending, print digest to stdout

Run with built-in daily schedule:
  python main.py --schedule --email --ntfy
"""
import argparse
import sys

from news_fetcher import fetch_tech_news
from summarizer import summarize_with_openai, summarize_article_brief
from email_sender import send_digest_email
from ntfy_sender import send_digest_to_ntfy, ntfy_configured, NTFY_ACTIONS_MAX
from article_fetcher import fetch_article_text
from config import EMAIL_TO, SMTP_USER, SMTP_PASSWORD, MAX_ARTICLES

# Number of articles to fetch, summarize, and send (aligned with ntfy Actions)
DIGEST_SIZE = MAX_ARTICLES


def run_digest(
    *,
    dry_run: bool = False,
    send_email: bool = False,
    send_ntfy: bool = False,
) -> None:
    """Fetch news, summarize, and optionally send digest via email and/or ntfy."""
    print("Fetching tech news...")
    items = fetch_tech_news(max_articles=DIGEST_SIZE)
    if not items:
        print("No articles fetched. Skipping send.")
        return
    print(f"Got {len(items)} articles. Summarizing...")
    summary = summarize_with_openai(items)
    if dry_run:
        print("--- DRY RUN: digest (no email/ntfy sent) ---")
        print(summary)
        print("--- end ---")
        return
    if send_email:
        print("Sending email...")
        send_digest_email(summary)
    if send_ntfy:
        print("Sending to ntfy...")
        try:
            # Brief 2-3 sentence summaries from original article text (canonical URL already resolved in fetch)
            ntfy_items = items[:NTFY_ACTIONS_MAX]
            brief_summaries = []
            for i, item in enumerate(ntfy_items):
                print(f"  Fetching article {i + 1}/{len(ntfy_items)}...")
                text = fetch_article_text(item.link)
                brief = summarize_article_brief(item.title, text) if text else ""
                brief_summaries.append(brief or "")
            send_digest_to_ntfy(items, summaries=brief_summaries)
        except Exception as e:
            print(f"Warning: ntfy send failed: {e}")
    print("Done.")


def run_scheduled(*, send_email: bool = False, send_ntfy: bool = False) -> None:
    """Run the digest three times a day at 08:00, 15:00 and 22:00 (local time)."""
    try:
        import schedule
    except ImportError:
        print("Install 'schedule' for --schedule: pip install schedule")
        sys.exit(1)

    def job() -> None:
        run_digest(send_email=send_email, send_ntfy=send_ntfy)

    for at_time in ("08:00", "15:00", "22:00"):
        schedule.every().day.at(at_time).do(job)
    print("Scheduler started. Runs at 08:00, 15:00, 22:00. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        import time
        time.sleep(60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tech News Summarizer")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run digest three times a day (08:00, 15:00, 22:00) instead of once",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and summarize only; do not send anywhere",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Send digest by email (requires EMAIL_TO, SMTP_USER, SMTP_PASSWORD in environment)",
    )
    parser.add_argument(
        "--ntfy",
        action="store_true",
        help="Send digest to ntfy (requires NTFY_BASE_URL and NTFY_TOPIC in environment)",
    )
    args = parser.parse_args()

    if not args.dry_run:
        if not args.email and not args.ntfy:
            print("Error: Without --dry-run, specify at least one of --email or --ntfy.")
            sys.exit(1)
        if args.email:
            if not EMAIL_TO or not SMTP_USER or not SMTP_PASSWORD:
                print("Error: For --email, set EMAIL_TO, SMTP_USER and SMTP_PASSWORD in environment (SMTP_PASSWORD via Docker secret or env).")
                sys.exit(1)
        if args.ntfy and not ntfy_configured():
            print("Error: For --ntfy, set NTFY_BASE_URL and NTFY_TOPIC in environment.")
            sys.exit(1)

    if args.schedule:
        run_scheduled(send_email=args.email, send_ntfy=args.ntfy)
    else:
        run_digest(
            dry_run=args.dry_run,
            send_email=args.email,
            send_ntfy=args.ntfy,
        )


if __name__ == "__main__":
    main()
