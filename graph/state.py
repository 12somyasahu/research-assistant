# graph/state.py
# This file defines the "shared brain" of our multi-agent system.
# Every agent reads from and writes to this state — think of it
# as a whiteboard all four agents are staring at.

from typing import TypedDict, List, Optional


class ResearchState(TypedDict):
    """
    The single source of truth passed between every agent in the graph.

    LangGraph passes this around like a baton in a relay race.
    Each agent picks it up, does their job, adds their piece, and hands it off.
    """

    # The user's original research topic — never touched after it's set
    topic: str

    # Raw search results from Tavily (list of dicts with title, url, content)
    search_results: List[dict]

    # Agent 2's cleaned-up summary of all the raw search noise
    summary: str

    # Agent 3's fact-check report — a list of validated (or disputed) claims
    fact_check_report: List[str]

    # The final polished report that the user actually sees
    final_report: str

    # Tracks which step we're on — useful for the UI progress bar
    current_step: str

    # If anything explodes, the error lands here instead of crashing the whole app
    error: Optional[str]
