import logging
from datetime import datetime, timedelta, timezone

from apify_client import ApifyClient

from src.config import get_settings
from src.models import ContentItem, ContentSource

logger = logging.getLogger(__name__)


def fetch_twitter_items(list_urls: list[str] | None = None, handles: list[str] | None = None, hours_back: int = 24) -> list[ContentItem]:
    """Fetch recent tweets from Twitter lists and individual accounts using Apify tweet-scraper."""
    s = get_settings()
    urls = list_urls or s.twitter_lists
    handle_list = handles or s.twitter_handle_list

    if not urls and not handle_list:
        logger.warning("No Twitter list URLs or handles configured")
        return []

    if not s.apify_api_token:
        logger.warning("Apify API token not configured")
        return []

    client = ApifyClient(s.apify_api_token)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    items: list[ContentItem] = []

    since_date = cutoff.strftime("%Y-%m-%d")
    until_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

    run_input = {
        "maxTweets": 10,
        "sinceDate": since_date,
        "untilDate": until_date,
    }
    if urls:
        run_input["listUrls"] = urls
    if handle_list:
        run_input["twitterHandles"] = handle_list

    try:
        logger.info(f"Starting Apify tweet-scraper: {len(urls)} lists, {len(handle_list)} handles")
        run = client.actor("apidojo/tweet-scraper").call(run_input=run_input)
        dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        logger.info(f"Apify returned {len(dataset_items)} raw tweets")

        for tweet in dataset_items:
            try:
                # Apify tweet-scraper uses these field names
                text = tweet.get("text") or tweet.get("fullText") or tweet.get("full_text", "")
                if not text:
                    continue

                # Get tweet URL directly, or build from author + id
                tweet_url = tweet.get("url") or tweet.get("twitterUrl", "")
                if not tweet_url:
                    author_info = tweet.get("author", {})
                    screen_name = author_info.get("userName", "")
                    tweet_id = tweet.get("id", tweet.get("id_str", ""))
                    if screen_name and tweet_id:
                        tweet_url = f"https://x.com/{screen_name}/status/{tweet_id}"
                if not tweet_url:
                    continue

                # Get author name
                author_info = tweet.get("author", tweet.get("user", {}))
                screen_name = author_info.get("userName", author_info.get("screen_name", ""))

                # Parse date
                created_at_str = tweet.get("createdAt", tweet.get("created_at", ""))
                published = _parse_twitter_date(created_at_str)

                # Skip retweets (usually just noise)
                if text.startswith("RT @"):
                    continue

                # Truncate long tweets
                snippet = text[:500] + "..." if len(text) > 500 else text

                items.append(ContentItem(
                    source=ContentSource.TWITTER,
                    title=snippet[:120],
                    url=tweet_url,
                    author=f"@{screen_name}" if screen_name else "",
                    content_snippet=snippet,
                    published_at=published,
                ))
            except Exception as e:
                logger.warning(f"Error parsing tweet: {e}")
                continue

        logger.info(f"Fetched {len(items)} tweets total")
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
