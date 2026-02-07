import logging
import sys
from datetime import date

from src.config import get_settings
from src.db import (
    get_learning_context,
    insert_digest_items,
    get_digest_items,
    mark_items_emailed,
    upsert_digest_log,
    calculate_precision_for_date,
)
from src.models import ContentItem
from src.ingestion.newsletters import fetch_rss_items
from src.ingestion.youtube import fetch_youtube_items
from src.ingestion.twitter import fetch_twitter_items
from src.scoring.scorer import score_items
from src.digest.builder import build_digest
from src.delivery.emailer import send_digest_email
from src.monitoring.precision import check_precision_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Main daily pipeline orchestrator."""
    today = date.today()
    logger.info(f"Starting daily pipeline for {today}")
    upsert_digest_log(today, status="running")

    try:
        # 1. Load learning context
        context = get_learning_context()
        logger.info(f"Loaded learning context: goals={context.goals[:80]}...")

        # 2. Ingest from all sources (isolated errors)
        all_items: list[ContentItem] = []

        for name, fetcher in [
            ("newsletters", fetch_rss_items),
            ("youtube", fetch_youtube_items),
            ("twitter", fetch_twitter_items),
        ]:
            try:
                items = fetcher()
                logger.info(f"{name}: fetched {len(items)} items")
                all_items.extend(items)
            except Exception as e:
                logger.error(f"{name} ingestion failed: {e}")

        logger.info(f"Total ingested: {len(all_items)} items")

        # 3. Deduplicate by URL
        seen_urls = set()
        unique_items: list[ContentItem] = []
        for item in all_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)
        logger.info(f"After dedup: {len(unique_items)} unique items")

        # 4. Score with GPT-4o
        scored_items = score_items(unique_items, context)
        logger.info(f"Scored {len(scored_items)} items")

        # 5. Store in DB
        stored = insert_digest_items(scored_items, today)
        logger.info(f"Stored {len(stored)} items in DB")

        # 6. Build digest
        db_items = get_digest_items(today)
        html, included_ids = build_digest(db_items, today)

        # 7. Send email
        email_sent = send_digest_email(html, today)
        if email_sent:
            mark_items_emailed(included_ids)
            logger.info(f"Digest sent with {len(included_ids)} items")
        else:
            logger.error("Failed to send digest email")

        # 8. Check precision from previous days
        check_precision_alert()

        # 9. Log completion
        upsert_digest_log(
            today,
            status="completed",
            items_ingested=len(all_items),
            items_scored=len(scored_items),
            items_emailed=len(included_ids) if email_sent else 0,
        )
        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        upsert_digest_log(today, status="failed", error_message=str(e))
        raise


if __name__ == "__main__":
    run_pipeline()
