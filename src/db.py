from datetime import date, datetime
from typing import Optional

from supabase import create_client, Client

from src.config import get_settings
from src.models import LearningContext, ScoredItem, ContentSource


def get_client() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


# --- Learning Context ---

def get_learning_context(client: Optional[Client] = None) -> LearningContext:
    client = client or get_client()
    result = client.table("learning_context").select("*").eq("id", 1).single().execute()
    row = result.data
    return LearningContext(
        goals=row["goals"],
        digest_format=row["digest_format"],
        methodology=row["methodology"],
        skill_levels=row["skill_levels"],
        time_availability=row["time_availability"],
        project_context=row["project_context"],
    )


def update_learning_context(ctx: LearningContext, client: Optional[Client] = None) -> None:
    client = client or get_client()
    # Save history snapshot first
    current = get_learning_context(client)
    client.table("learning_context_history").insert({
        "snapshot": current.model_dump(),
    }).execute()

    # Update the single row
    client.table("learning_context").update({
        "goals": ctx.goals,
        "digest_format": ctx.digest_format,
        "methodology": ctx.methodology,
        "skill_levels": ctx.skill_levels,
        "time_availability": ctx.time_availability,
        "project_context": ctx.project_context,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", 1).execute()


# --- Digest Items ---

def insert_digest_items(items: list[ScoredItem], digest_date: date, client: Optional[Client] = None) -> list[dict]:
    client = client or get_client()
    rows = []
    for item in items:
        rows.append({
            "digest_date": digest_date.isoformat(),
            "source": item.source.value,
            "title": item.title,
            "url": item.url,
            "author": item.author,
            "content_snippet": item.content_snippet,
            "score": float(item.score),
            "justification": item.justification,
        })
    if not rows:
        return []
    result = client.table("digest_items").upsert(
        rows, on_conflict="url,digest_date"
    ).execute()
    return result.data


def get_digest_items(digest_date: date, min_score: float = 0.0, client: Optional[Client] = None) -> list[dict]:
    client = client or get_client()
    result = (
        client.table("digest_items")
        .select("*")
        .eq("digest_date", digest_date.isoformat())
        .gte("score", min_score)
        .order("score", desc=True)
        .execute()
    )
    return result.data


def mark_items_emailed(item_ids: list[str], client: Optional[Client] = None) -> None:
    client = client or get_client()
    for item_id in item_ids:
        client.table("digest_items").update(
            {"included_in_email": True}
        ).eq("id", item_id).execute()


# --- Feedback ---

def log_feedback(item_id: str, response: str, client: Optional[Client] = None) -> dict:
    client = client or get_client()
    result = client.table("feedback").insert({
        "item_id": item_id,
        "response": response,
    }).execute()
    return result.data[0] if result.data else {}


def get_feedback_for_date(digest_date: date, client: Optional[Client] = None) -> list[dict]:
    client = client or get_client()
    result = (
        client.table("feedback")
        .select("*, digest_items!inner(digest_date)")
        .eq("digest_items.digest_date", digest_date.isoformat())
        .execute()
    )
    return result.data


# --- Digest Log ---

def upsert_digest_log(
    digest_date: date,
    status: str = "running",
    items_ingested: int = 0,
    items_scored: int = 0,
    items_emailed: int = 0,
    precision_rate: Optional[float] = None,
    error_message: Optional[str] = None,
    cost_openai_usd: float = 0,
    cost_apify_usd: float = 0,
    cost_resend_usd: float = 0,
    cost_total_usd: float = 0,
    openai_tokens_used: int = 0,
    client: Optional[Client] = None,
) -> None:
    client = client or get_client()
    row = {
        "digest_date": digest_date.isoformat(),
        "status": status,
        "items_ingested": items_ingested,
        "items_scored": items_scored,
        "items_emailed": items_emailed,
        "cost_openai_usd": cost_openai_usd,
        "cost_apify_usd": cost_apify_usd,
        "cost_resend_usd": cost_resend_usd,
        "cost_total_usd": cost_total_usd,
        "openai_tokens_used": openai_tokens_used,
    }
    if precision_rate is not None:
        row["precision_rate"] = float(precision_rate)
    if error_message is not None:
        row["error_message"] = error_message
    if status == "completed":
        row["completed_at"] = datetime.utcnow().isoformat()

    client.table("digest_log").upsert(row, on_conflict="digest_date").execute()


# --- Precision Queries ---

def get_precision_stats(days: int = 7, client: Optional[Client] = None) -> list[dict]:
    """Get daily precision rates for the last N days."""
    client = client or get_client()
    result = (
        client.table("digest_log")
        .select("digest_date, precision_rate, items_emailed")
        .not_.is_("precision_rate", "null")
        .order("digest_date", desc=True)
        .limit(days)
        .execute()
    )
    return result.data


def get_daily_cost(target_date: date, client: Optional[Client] = None) -> float:
    """Get total cost for a specific date."""
    client = client or get_client()
    result = (
        client.table("digest_log")
        .select("cost_total_usd")
        .eq("digest_date", target_date.isoformat())
        .execute()
    )
    if result.data:
        return float(result.data[0].get("cost_total_usd", 0) or 0)
    return 0.0


def get_monthly_cost(year: int, month: int, client: Optional[Client] = None) -> float:
    """Sum cost_total_usd for all runs in a given month."""
    client = client or get_client()
    start = date(year, month, 1).isoformat()
    if month == 12:
        end = date(year + 1, 1, 1).isoformat()
    else:
        end = date(year, month + 1, 1).isoformat()
    result = (
        client.table("digest_log")
        .select("cost_total_usd")
        .gte("digest_date", start)
        .lt("digest_date", end)
        .execute()
    )
    return sum(float(r.get("cost_total_usd", 0) or 0) for r in result.data)


def calculate_precision_for_date(digest_date: date, client: Optional[Client] = None) -> Optional[float]:
    """Calculate precision = useful / (useful + not_useful) for a given date."""
    client = client or get_client()
    feedback = get_feedback_for_date(digest_date, client)
    if not feedback:
        return None
    useful = sum(1 for f in feedback if f["response"] == "useful")
    total = len(feedback)
    return round(useful / total * 100, 2) if total > 0 else None
