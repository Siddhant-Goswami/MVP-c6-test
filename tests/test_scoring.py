from src.scoring.scorer import _build_system_prompt, _build_user_prompt


def test_build_system_prompt(sample_context):
    prompt = _build_system_prompt(sample_context)
    assert "Building AI-powered applications" in prompt
    assert "Python: advanced" in prompt
    assert "practical" in prompt
    assert "0-10" in prompt


def test_build_user_prompt(sample_items):
    prompt = _build_user_prompt(sample_items)
    assert "Item 1" in prompt
    assert "Item 2" in prompt
    assert "Item 3" in prompt
    assert "Building RAG Systems" in prompt
    assert "newsletter" in prompt
