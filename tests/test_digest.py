from datetime import date
from unittest.mock import patch, MagicMock

from src.digest.builder import build_digest


def _mock_settings():
    s = MagicMock()
    s.feedback_api_url = "http://localhost:8000"
    s.streamlit_app_url = ""
    return s


@patch("src.digest.builder.get_settings", _mock_settings)
def test_build_digest_with_items():
    items = [
        {"id": "1", "source": "newsletter", "title": "Article A", "url": "https://a.com", "score": 9.0, "justification": "Very relevant", "author": "Author A"},
        {"id": "2", "source": "youtube", "title": "Video B", "url": "https://b.com", "score": 7.5, "justification": "Good match", "author": "Author B"},
        {"id": "3", "source": "twitter", "title": "Tweet C", "url": "https://c.com", "score": 6.0, "justification": "Related", "author": "Author C"},
        {"id": "4", "source": "newsletter", "title": "Article D", "url": "https://d.com", "score": 3.0, "justification": "Not very relevant", "author": "Author D"},
    ]
    html, included_ids = build_digest(items, date(2025, 1, 15))

    assert "Article A" in html
    assert "Video B" in html
    assert "Tweet C" in html
    # Article D has score < 5.0, should not be included
    assert "Article D" not in html
    assert len(included_ids) == 3


@patch("src.digest.builder.get_settings", _mock_settings)
def test_build_digest_empty():
    html, included_ids = build_digest([], date(2025, 1, 15))
    assert "No items matched" in html
    assert len(included_ids) == 0
