import pytest

from src.models import ContentItem, ContentSource, LearningContext


@pytest.fixture
def sample_items():
    return [
        ContentItem(
            source=ContentSource.NEWSLETTER,
            title="Building RAG Systems with LangChain",
            url="https://example.com/rag-langchain",
            author="John Doe",
            content_snippet="A practical guide to building retrieval-augmented generation systems...",
        ),
        ContentItem(
            source=ContentSource.YOUTUBE,
            title="System Design Interview: Rate Limiter",
            url="https://youtube.com/watch?v=abc123",
            author="Tech Channel",
            content_snippet="In this video we design a distributed rate limiter...",
        ),
        ContentItem(
            source=ContentSource.TWITTER,
            title="Thread on async Python patterns",
            url="https://twitter.com/user/status/123",
            author="@pythonista",
            content_snippet="Here are 5 async Python patterns I use daily in production...",
        ),
    ]


@pytest.fixture
def sample_context():
    return LearningContext(
        goals="Building AI-powered applications, improving Python skills",
        methodology={"style": "practical", "depth": "intermediate", "consumption": "30min"},
        skill_levels={"Python": "advanced", "ML": "intermediate"},
        time_availability="30 minutes per day",
        project_context="Building a content curation SaaS",
    )
