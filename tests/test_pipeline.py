from src.models import ContentItem, ScoredItem, ContentSource, LearningContext


def test_dedup_logic():
    """Test the deduplication logic used in pipeline."""
    items = [
        ContentItem(source=ContentSource.NEWSLETTER, title="A", url="https://a.com"),
        ContentItem(source=ContentSource.TWITTER, title="A dup", url="https://a.com"),
        ContentItem(source=ContentSource.YOUTUBE, title="B", url="https://b.com"),
    ]
    seen = set()
    unique = []
    for item in items:
        if item.url not in seen:
            seen.add(item.url)
            unique.append(item)
    assert len(unique) == 2
    assert unique[0].title == "A"
    assert unique[1].title == "B"


def test_scored_item_validation():
    item = ScoredItem(
        source=ContentSource.NEWSLETTER,
        title="Test",
        url="https://test.com",
        score=8.5,
        justification="Good content",
    )
    assert item.score == 8.5
    assert 0.0 <= item.score <= 10.0
