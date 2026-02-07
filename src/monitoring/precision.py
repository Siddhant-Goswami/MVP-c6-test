import logging
from datetime import date, timedelta

from src.db import calculate_precision_for_date, upsert_digest_log, get_precision_stats
from src.delivery.emailer import send_alert_email

logger = logging.getLogger(__name__)

LOW_PRECISION_THRESHOLD = 60.0  # percent
ALERT_CONSECUTIVE_DAYS = 3


def check_precision_alert():
    """Check precision from recent days and send alert if consistently low."""
    today = date.today()

    # Calculate and store precision for last few days
    for days_ago in range(1, ALERT_CONSECUTIVE_DAYS + 1):
        check_date = today - timedelta(days=days_ago)
        precision = calculate_precision_for_date(check_date)
        if precision is not None:
            upsert_digest_log(check_date, status="completed", precision_rate=precision)
            logger.info(f"Precision for {check_date}: {precision}%")

    # Check if last N days are all below threshold
    stats = get_precision_stats(days=ALERT_CONSECUTIVE_DAYS)
    if len(stats) < ALERT_CONSECUTIVE_DAYS:
        logger.info("Not enough data for precision alert check")
        return

    low_days = [
        s for s in stats
        if s.get("precision_rate") is not None and float(s["precision_rate"]) < LOW_PRECISION_THRESHOLD
    ]

    if len(low_days) >= ALERT_CONSECUTIVE_DAYS:
        rates = [f"{s['digest_date']}: {s['precision_rate']}%" for s in low_days]
        body = (
            f"Precision has been below {LOW_PRECISION_THRESHOLD}% for {ALERT_CONSECUTIVE_DAYS} consecutive days.\n\n"
            + "\n".join(rates)
            + "\n\nConsider updating your learning context to better match your interests."
        )
        send_alert_email(
            subject="⚠️ Learning Feed: Low Precision Alert",
            body=body,
        )
        logger.warning(f"Low precision alert sent: {rates}")
    else:
        logger.info("Precision is within acceptable range")
