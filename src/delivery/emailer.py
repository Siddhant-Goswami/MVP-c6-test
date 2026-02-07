import logging
from datetime import date

import resend

from src.config import get_settings

logger = logging.getLogger(__name__)


def send_digest_email(html: str, digest_date: date) -> bool:
    """Send the digest email via Resend."""
    s = get_settings()
    resend.api_key = s.resend_api_key

    subject = f"🎓 Your Learning Digest — {digest_date.strftime('%b %d, %Y')}"

    try:
        response = resend.Emails.send({
            "from": s.digest_from_email,
            "to": [s.digest_recipient_email],
            "subject": subject,
            "html": html,
        })
        logger.info(f"Digest email sent: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to send digest email: {e}")
        return False


def send_alert_email(subject: str, body: str) -> bool:
    """Send an alert email (e.g., low precision warning)."""
    s = get_settings()
    resend.api_key = s.resend_api_key

    try:
        response = resend.Emails.send({
            "from": s.digest_from_email,
            "to": [s.digest_recipient_email],
            "subject": subject,
            "html": f"<p>{body}</p>",
        })
        logger.info(f"Alert email sent: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
        return False
