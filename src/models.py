from datetime import datetime, date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ContentSource(str, Enum):
    TWITTER = "twitter"
    NEWSLETTER = "newsletter"
    YOUTUBE = "youtube"


class ContentItem(BaseModel):
    source: ContentSource
    title: str
    url: str
    author: str = ""
    content_snippet: str = ""
    published_at: Optional[datetime] = None


class ScoredItem(BaseModel):
    source: ContentSource
    title: str
    url: str
    author: str = ""
    content_snippet: str = ""
    score: float = Field(ge=0.0, le=10.0)
    justification: str = ""


class LearningContext(BaseModel):
    goals: str = ""
    digest_format: str = "daily"
    methodology: dict = Field(default_factory=lambda: {
        "style": "practical",
        "depth": "intermediate",
        "consumption": "30min",
    })
    skill_levels: dict = Field(default_factory=dict)
    time_availability: str = "30 minutes per day"
    project_context: str = ""


class FeedbackResponse(BaseModel):
    item_id: str
    response: str  # "useful" or "not_useful"


class DigestLog(BaseModel):
    digest_date: date
    status: str = "running"
    items_ingested: int = 0
    items_scored: int = 0
    items_emailed: int = 0
    precision_rate: Optional[float] = None
    error_message: Optional[str] = None
