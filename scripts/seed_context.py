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
        "goals": "Building AI-powered applications, improving Python architecture skills",
        "digest_format": "daily",
        "methodology": {
            "style": "practical",
            "depth": "intermediate",
            "consumption": "30min",
        },
        "skill_levels": {
            "Python": "advanced",
            "Machine Learning": "intermediate",
            "System Design": "intermediate",
        },
        "time_availability": "30 minutes per day",
        "project_context": "",
    }).execute()

    print("Learning context seeded successfully!")


if __name__ == "__main__":
    seed()
