import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.config import get_settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
MIN_SCORE_FOR_EMAIL = 5.0
TOP_N = 3


def build_digest(items: list[dict], digest_date: date) -> tuple[str, list[str]]:
    """Build HTML digest email from scored items.

    Returns:
        Tuple of (html_content, list_of_item_ids_included)
    """
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("digest.html")

    # Filter items with score >= MIN_SCORE
    eligible = [i for i in items if float(i.get("score", 0)) >= MIN_SCORE_FOR_EMAIL]
    eligible.sort(key=lambda x: float(x.get("score", 0)), reverse=True)

    # Split into top 3 and remaining
    top_items = eligible[:TOP_N]
    remaining_items = eligible[TOP_N:]

    # Add feedback URLs
    s = get_settings()
    base_url = s.feedback_api_url.rstrip("/")
    for item in top_items + remaining_items:
        item_id = item.get("id", "")
        item["feedback_useful_url"] = f"{base_url}/feedback/{item_id}?response=useful"
        item["feedback_not_useful_url"] = f"{base_url}/feedback/{item_id}?response=not_useful"

    html = template.render(
        digest_date=digest_date.strftime("%B %d, %Y"),
        total_items=len(items),
        top_items=top_items,
        remaining_items=remaining_items,
        context_update_url=s.streamlit_app_url or None,
    )

    included_ids = [i["id"] for i in top_items + remaining_items if "id" in i]
    logger.info(f"Built digest: {len(top_items)} top + {len(remaining_items)} remaining items")
    return html, included_ids
