from src.models import ContentSource


def test_content_source_enum():
    assert ContentSource.TWITTER.value == "twitter"
    assert ContentSource.NEWSLETTER.value == "newsletter"
    assert ContentSource.YOUTUBE.value == "youtube"


def test_sample_items_structure(sample_items):
    assert len(sample_items) == 3
    sources = {item.source for item in sample_items}
    assert sources == {ContentSource.NEWSLETTER, ContentSource.YOUTUBE, ContentSource.TWITTER}
    for item in sample_items:
        assert item.title
        assert item.url
