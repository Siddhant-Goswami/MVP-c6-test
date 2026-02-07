import logging
from datetime import datetime, timedelta, timezone

from apify_client import ApifyClient

from src.config import get_settings
from src.models import ContentItem, ContentSource

logger = logging.getLogger(__name__)


def fetch_twitter_items(list_urls: list[str] | None = None, hours_back: int = 24) -> list[ContentItem]:
    """Fetch recent tweets from Twitter lists using Apify tweet-scraper."""
    s = get_settings()
    urls = list_urls or s.twitter_lists
    if not urls:
        logger.warning("No Twitter list URLs configured")
        return []

    if not s.apify_api_token:
        logger.warning("Apify API token not configured")
        return []

    client = ApifyClient(s.apify_api_token)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    items: list[ContentItem] = []

    since_date = cutoff.strftime("%Y-%m-%d")
    until_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        run_input = {
            "listUrls": urls,
            "maxTweets": 50,
            "sinceDate": since_date,
            "untilDate": until_date,
        }

        run = client.actor("apidojo/tweet-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).iterate_items()

        for tweet in dataset_items:
            try:
                text = tweet.get("full_text") or tweet.get("text", "")
                if not text:
                    continue

                # Build tweet URL
                user = tweet.get("user", {})
                screen_name = user.get("screen_name", "")
                tweet_id = tweet.get("id_str", "")
                url = f"https://twitter.com/{screen_name}/status/{tweet_id}" if screen_name and tweet_id else ""
                if not url:
                    continue

                # Parse date
                created_at_str = tweet.get("created_at", "")
                published = _parse_twitter_date(created_at_str)

                # Truncate long tweets
                snippet = text[:500] + "..." if len(text) > 500 else text

                items.append(ContentItem(
                    source=ContentSource.TWITTER,
                    title=snippet[:120],  # Use first 120 chars as title
                    url=url,
                    author=f"@{screen_name}" if screen_name else "",
                    content_snippet=snippet,
                    published_at=published,
                ))
            except Exception as e:
                logger.warning(f"Error parsing tweet: {e}")
                continue

        logger.info(f"Fetched {len(items)} tweets from lists")
    except Exception as e:
        logger.error(f"Error fetching tweets from Apify: {e}")

    return items


def _parse_twitter_date(date_str: str) -> datetime | None:
    """Parse Twitter's date format: 'Thu Oct 26 14:30:00 +0000 2023'."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        return None
