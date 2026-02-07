"""Seed default learning context for first run."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import get_client


def seed():
    client = get_client()

    # Check if already seeded
    result = client.table("learning_context").select("id").eq("id", 1).execute()
    if result.data:
        print("Learning context already exists. Updating with defaults...")

    client.table("learning_context").upsert({
        "id": 1,
        "goals": "Agentic coding workflows and tooling, AI/ML engineering best practices, LLM economics and scaling, CLI-first development patterns, strategic implications of AI for businesses",
        "digest_format": "daily",
        "methodology": {
            "style": "practical",
            "depth": "advanced",
            "consumption": "30min",
        },
        "skill_levels": {
            "Python": "advanced",
            "AI/ML Engineering": "advanced",
            "Agentic Coding": "intermediate",
            "System Design": "intermediate",
            "LLM APIs": "advanced",
        },
        "time_availability": "30 minutes per day",
        "project_context": "Building AI-powered developer tools. Interested in cutting-edge agentic coding, compound AI systems, and practical workflows over theoretical content.",
    }).execute()

    print("Learning context seeded successfully!")


if __name__ == "__main__":
    seed()
