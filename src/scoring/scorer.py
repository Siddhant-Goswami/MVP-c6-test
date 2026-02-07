import json
import logging

from openai import OpenAI

from src.config import get_settings
from src.models import ContentItem, ScoredItem, LearningContext, CostTracker

logger = logging.getLogger(__name__)

BATCH_SIZE = 12


def score_items(items: list[ContentItem], context: LearningContext, tracker: CostTracker | None = None) -> list[ScoredItem]:
    """Score content items against the learning context using GPT-4o."""
    if not items:
        return []

    client = OpenAI(api_key=get_settings().openai_api_key)
    scored: list[ScoredItem] = []

    # Process in batches
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        try:
            batch_scored = _score_batch(client, batch, context, tracker)
            scored.extend(batch_scored)
        except Exception as e:
            logger.error(f"Error scoring batch {i // BATCH_SIZE + 1}: {e}")
            # On failure, assign default score of 0 so items aren't lost
            for item in batch:
                scored.append(ScoredItem(
                    source=item.source,
                    title=item.title,
                    url=item.url,
                    author=item.author,
                    content_snippet=item.content_snippet,
                    score=0.0,
                    justification="Scoring failed",
                ))

    logger.info(f"Scored {len(scored)} items total")
    return scored


def _score_batch(client: OpenAI, items: list[ContentItem], context: LearningContext, tracker: CostTracker | None = None) -> list[ScoredItem]:
    """Score a batch of items with a single GPT-4o call."""
    system_prompt = _build_system_prompt(context)
    user_prompt = _build_user_prompt(items)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    # Track token usage
    if tracker and response.usage:
        tracker.add_openai_usage(response.usage.prompt_tokens, response.usage.completion_tokens)
        logger.debug(f"OpenAI tokens: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion")

    content = response.choices[0].message.content
    result = json.loads(content)
    scores = result.get("scores", [])

    scored_items: list[ScoredItem] = []
    for idx, item in enumerate(items):
        if idx < len(scores):
            s = scores[idx]
            score = max(0.0, min(10.0, float(s.get("score", 0))))
            justification = s.get("justification", "")
        else:
            score = 0.0
            justification = "No score returned"

        scored_items.append(ScoredItem(
            source=item.source,
            title=item.title,
            url=item.url,
            author=item.author,
            content_snippet=item.content_snippet,
            score=score,
            justification=justification,
        ))

    return scored_items


def _build_system_prompt(context: LearningContext) -> str:
    skill_str = ", ".join(f"{k}: {v}" for k, v in context.skill_levels.items()) if context.skill_levels else "Not specified"
    methodology = context.methodology or {}

    return f"""You are a learning content curator. Score each content item on a scale of 0-10 based on how relevant and valuable it is for the user's learning goals.

## User's Learning Context
- **Goals**: {context.goals or 'Not specified'}
- **Skill Levels**: {skill_str}
- **Learning Style**: {methodology.get('style', 'practical')}
- **Depth Preference**: {methodology.get('depth', 'intermediate')}
- **Time Available**: {context.time_availability}
- **Current Project**: {context.project_context or 'None'}

## Scoring Criteria
- 8-10: Directly relevant to current goals/project, actionable, right skill level
- 5-7: Related to goals, useful but not immediately actionable
- 3-4: Tangentially related, might be useful later
- 0-2: Not relevant to current learning focus

## Response Format
Return a JSON object with a "scores" array. Each element must have:
- "score": number between 0 and 10 (one decimal place)
- "justification": brief explanation (1-2 sentences)

The array must have exactly one entry per input item, in the same order."""


def _build_user_prompt(items: list[ContentItem]) -> str:
    lines = ["Score the following content items:\n"]
    for idx, item in enumerate(items):
        lines.append(f"### Item {idx + 1}")
        lines.append(f"- **Source**: {item.source.value}")
        lines.append(f"- **Title**: {item.title}")
        lines.append(f"- **Author**: {item.author}")
        lines.append(f"- **Snippet**: {item.content_snippet}")
        lines.append("")
    return "\n".join(lines)
