from dataclasses import dataclass
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


# Pricing constants
OPENAI_GPT4O_INPUT_PER_1K = 0.0025
OPENAI_GPT4O_OUTPUT_PER_1K = 0.01
RESEND_COST_PER_EMAIL = 0.00028  # after free tier


@dataclass
class CostTracker:
    openai_prompt_tokens: int = 0
    openai_completion_tokens: int = 0
    openai_cost_usd: float = 0.0
    apify_cost_usd: float = 0.0
    resend_emails_sent: int = 0
    resend_cost_usd: float = 0.0

    @property
    def total_cost_usd(self) -> float:
        return self.openai_cost_usd + self.apify_cost_usd + self.resend_cost_usd

    def add_openai_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.openai_prompt_tokens += prompt_tokens
        self.openai_completion_tokens += completion_tokens
        cost = (prompt_tokens * OPENAI_GPT4O_INPUT_PER_1K + completion_tokens * OPENAI_GPT4O_OUTPUT_PER_1K) / 1000
        self.openai_cost_usd += cost

    def add_apify_cost(self, cost_usd: float) -> None:
        self.apify_cost_usd += cost_usd

    def add_resend_email(self) -> None:
        self.resend_emails_sent += 1
        self.resend_cost_usd = self.resend_emails_sent * RESEND_COST_PER_EMAIL

    @property
    def openai_total_tokens(self) -> int:
        return self.openai_prompt_tokens + self.openai_completion_tokens
