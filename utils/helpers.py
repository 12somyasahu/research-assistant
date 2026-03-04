# utils/helpers.py
# Small utility functions that didn't fit anywhere else.
# Classic "miscellaneous" file that every project eventually needs.

import os
from dotenv import load_dotenv


def load_env():
    """Load .env file. Call this once at app startup."""
    load_dotenv()


def check_api_keys() -> tuple[bool, list[str]]:
    """
    Validates that all required API keys are present before we start a run.
    Returns (all_good: bool, missing_keys: list[str]).
    """
    # updated to Groq — no more Gemini
    required_keys = ["GROQ_API_KEY", "TAVILY_API_KEY"]
    missing = [key for key in required_keys if not os.getenv(key)]
    return (len(missing) == 0, missing)


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncates text for display purposes."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def count_words(text: str) -> int:
    """Quick word count — used to show report stats in the UI."""
    return len(text.split())


def reading_time(text: str) -> int:
    """
    Estimates reading time in minutes.
    Average adult reads ~200 words per minute — rounds up to nearest minute.
    """
    words = count_words(text)
    minutes = max(1, round(words / 200))
    return minutes


def extract_source_urls(search_results: list) -> list[dict]:
    """
    Pulls clean title+url pairs from raw search results.
    Filters out the Tavily Quick Answer pseudo-entry.
    """
    return [
        {"title": r.get("title", "Untitled"), "url": r.get("url", "#")}
        for r in search_results
        if r.get("url", "N/A") != "N/A"
    ]
