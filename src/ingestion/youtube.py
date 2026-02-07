import logging
from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from src.config import get_settings
from src.models import ContentItem, ContentSource

logger = logging.getLogger(__name__)


def fetch_youtube_items(channel_ids: list[str] | None = None, hours_back: int = 24) -> list[ContentItem]:
    """Fetch recent videos from YouTube channels using the Data API v3."""
    s = get_settings()
    ids = channel_ids or s.youtube_channels
    if not ids:
        logger.warning("No YouTube channel IDs configured")
        return []

    if not s.youtube_api_key:
        logger.warning("YouTube API key not configured")
        return []

    youtube = build("youtube", "v3", developerKey=s.youtube_api_key)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    items: list[ContentItem] = []

    for channel_id in ids:
        try:
            # Convert channel ID to uploads playlist ID (UC -> UU trick)
            uploads_playlist_id = "UU" + channel_id[2:] if channel_id.startswith("UC") else channel_id

            response = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=10,
            ).execute()

            for video in response.get("items", []):
                snippet = video["snippet"]
                published_str = snippet.get("publishedAt", "")
                published = None
                if published_str:
                    published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                    if published < cutoff:
                        continue

                video_id = snippet.get("resourceId", {}).get("videoId", "")
                if not video_id:
                    continue

                title = snippet.get("title", "").strip()
                description = snippet.get("description", "")
                if len(description) > 500:
                    description = description[:500] + "..."

                items.append(ContentItem(
                    source=ContentSource.YOUTUBE,
                    title=title,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    author=snippet.get("channelTitle", ""),
                    content_snippet=description,
                    published_at=published,
                ))

            logger.info(f"Fetched videos from channel {channel_id}")
        except Exception as e:
            logger.error(f"Error fetching YouTube channel {channel_id}: {e}")
            continue

    logger.info(f"Total YouTube items: {len(items)}")
    return items
