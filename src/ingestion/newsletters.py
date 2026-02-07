import logging
from datetime import datetime, timedelta, timezone

import feedparser

from src.config import get_settings
from src.models import ContentItem, ContentSource

logger = logging.getLogger(__name__)


def fetch_rss_items(feed_urls: list[str] | None = None, hours_back: int = 24) -> list[ContentItem]:
    """Fetch recent items from RSS feeds."""
    urls = feed_urls or get_settings().rss_feeds
    if not urls:
        logger.warning("No RSS feed URLs configured")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    items: list[ContentItem] = []

    for url in urls:
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                logger.warning(f"Failed to parse feed {url}: {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                published = _parse_date(entry)
                if published and published < cutoff:
                    continue

                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue

                author = entry.get("author", "")
                summary = entry.get("summary", "")
                # Truncate summary to ~500 chars
                if len(summary) > 500:
                    summary = summary[:500] + "..."

                items.append(ContentItem(
                    source=ContentSource.NEWSLETTER,
                    title=title,
                    url=link,
                    author=author,
                    content_snippet=summary,
                    published_at=published,
                ))

            logger.info(f"Fetched {len(feed.entries)} entries from {url}")
        except Exception as e:
            logger.error(f"Error fetching feed {url}: {e}")
            continue

    logger.info(f"Total newsletter items: {len(items)}")
    return items


def _parse_date(entry) -> datetime | None:
    """Parse published date from a feed entry."""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                from time import mktime
                return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
            except (ValueError, OverflowError):
                continue
    return None
