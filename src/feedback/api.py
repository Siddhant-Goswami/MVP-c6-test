import logging
from datetime import date

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from src.db import log_feedback, get_precision_stats
from src.pipeline import run_pipeline

logger = logging.getLogger(__name__)

app = FastAPI(title="Learning Feed Curator - Feedback API")


@app.get("/feedback/{item_id}", response_class=HTMLResponse)
async def record_feedback(item_id: str, response: str = Query(..., pattern="^(useful|not_useful)$")):
    """Record user feedback from email link click."""
    try:
        log_feedback(item_id, response)
        emoji = "👍" if response == "useful" else "👎"
        label = "useful" if response == "useful" else "not useful"
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Feedback Recorded</title></head>
        <body style="display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:-apple-system,sans-serif;background:#f5f5f5;">
            <div style="text-align:center;background:white;padding:48px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                <div style="font-size:48px;margin-bottom:16px;">{emoji}</div>
                <h1 style="color:#1a1a2e;margin:0 0 8px;">Thanks!</h1>
                <p style="color:#666;">You marked this as <strong>{label}</strong>.</p>
                <p style="color:#888;font-size:14px;">This helps improve your future recommendations.</p>
            </div>
        </body>
        </html>
        """)
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        return HTMLResponse("<p>Error recording feedback. Please try again.</p>", status_code=500)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/stats")
async def stats(days: int = Query(default=7, ge=1, le=30)):
    """Get recent precision rates."""
    data = get_precision_stats(days)
    return {"days": days, "stats": data}


@app.post("/trigger")
async def trigger_pipeline():
    """Manually trigger the daily pipeline (dev only)."""
    try:
        run_pipeline()
        return {"status": "completed"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
