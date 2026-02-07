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
    get_daily_cost,
    get_monthly_cost,
)
from src.models import ContentItem, CostTracker
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
    settings = get_settings()
    tracker = CostTracker()
    logger.info(f"Starting daily pipeline for {today}")
    upsert_digest_log(today, status="running")

    try:
        # Budget check: monthly
        monthly_cost = get_monthly_cost(today.year, today.month)
        logger.info(f"Monthly cost so far: ${monthly_cost:.4f} / ${settings.monthly_budget_usd:.2f}")
        if monthly_cost >= settings.monthly_budget_usd:
            logger.warning(f"Monthly budget exceeded (${monthly_cost:.4f}/${settings.monthly_budget_usd:.2f}). Skipping pipeline.")
            upsert_digest_log(today, status="skipped_budget", error_message="Monthly budget exceeded")
            return

        # Budget check: daily
        daily_cost = get_daily_cost(today)
        logger.info(f"Daily cost so far: ${daily_cost:.4f} / ${settings.daily_budget_usd:.2f}")

        # 1. Load learning context
        context = get_learning_context()
        logger.info(f"Loaded learning context: goals={context.goals[:80]}...")

        # 2. Ingest from all sources (isolated errors)
        all_items: list[ContentItem] = []

        # Non-paid sources first
        for name, fetcher in [
            ("newsletters", fetch_rss_items),
            ("youtube", fetch_youtube_items),
        ]:
            try:
                items = fetcher()
                logger.info(f"{name}: fetched {len(items)} items")
                all_items.extend(items)
            except Exception as e:
                logger.error(f"{name} ingestion failed: {e}")

        # Twitter (Apify) — budget gated
        if monthly_cost + 0.50 <= settings.monthly_budget_usd:
            try:
                items = fetch_twitter_items(tracker=tracker)
                logger.info(f"twitter: fetched {len(items)} items")
                all_items.extend(items)
            except Exception as e:
                logger.error(f"twitter ingestion failed: {e}")
        else:
            logger.warning("Skipping Twitter ingestion to stay within monthly budget")

        logger.info(f"Total ingested: {len(all_items)} items")

        # 3. Deduplicate by URL
        seen_urls = set()
        unique_items: list[ContentItem] = []
        for item in all_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)
        logger.info(f"After dedup: {len(unique_items)} unique items")

        # 4. Score with GPT-4o — budget gated
        scored_items = []
        if daily_cost + tracker.total_cost_usd < settings.daily_budget_usd:
            scored_items = score_items(unique_items, context, tracker)
            logger.info(f"Scored {len(scored_items)} items")
        else:
            logger.warning(f"Daily budget exceeded (${daily_cost + tracker.total_cost_usd:.4f}/${settings.daily_budget_usd:.2f}). Skipping scoring.")

        # 5. Store in DB
        if scored_items:
            stored = insert_digest_items(scored_items, today)
            logger.info(f"Stored {len(stored)} items in DB")

        # 6. Build digest
        db_items = get_digest_items(today)
        html, included_ids = build_digest(db_items, today)

        # 7. Send email
        email_sent = send_digest_email(html, today, tracker)
        if email_sent:
            mark_items_emailed(included_ids)
            logger.info(f"Digest sent with {len(included_ids)} items")
        else:
            logger.error("Failed to send digest email")

        # 8. Check precision from previous days
        check_precision_alert()

        # 9. Log completion with cost data
        upsert_digest_log(
            today,
            status="completed",
            items_ingested=len(all_items),
            items_scored=len(scored_items),
            items_emailed=len(included_ids) if email_sent else 0,
            cost_openai_usd=tracker.openai_cost_usd,
            cost_apify_usd=tracker.apify_cost_usd,
            cost_resend_usd=tracker.resend_cost_usd,
            cost_total_usd=tracker.total_cost_usd,
            openai_tokens_used=tracker.openai_total_tokens,
        )

        # 10. Log cost summary
        new_monthly = monthly_cost + tracker.total_cost_usd
        logger.info(
            f"Cost: OpenAI=${tracker.openai_cost_usd:.4f} ({tracker.openai_total_tokens} tokens), "
            f"Apify=${tracker.apify_cost_usd:.4f}, Resend=${tracker.resend_cost_usd:.4f} | "
            f"Total=${tracker.total_cost_usd:.4f} | Monthly=${new_monthly:.4f}/${settings.monthly_budget_usd:.2f}"
        )
        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        upsert_digest_log(
            today,
            status="failed",
            error_message=str(e),
            cost_openai_usd=tracker.openai_cost_usd,
            cost_apify_usd=tracker.apify_cost_usd,
            cost_resend_usd=tracker.resend_cost_usd,
            cost_total_usd=tracker.total_cost_usd,
            openai_tokens_used=tracker.openai_total_tokens,
        )
        raise


if __name__ == "__main__":
    run_pipeline()
