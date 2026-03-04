# Agent 1: The Scout — goes out into the wild internet and brings back raw intel.
# Powered by Tavily, which is specifically built for AI search (way better than scraping).

import os
from tavily import TavilyClient
from graph.state import ResearchState


def search_agent(state: ResearchState) -> ResearchState:
    """
    Hits the Tavily search API and dumps raw results into state.
    Respects the search_depth setting passed in from the UI —
    'quick' gets 3 sources, 'deep' gets 7.
    """

    topic = state["topic"]
    # pull depth preference out of state — defaults to deep if not set
    depth = state.get("search_depth", "deep")
    max_results = 3 if depth == "quick" else 7

    # fires off the search, pray the API doesn't rate limit us
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    try:
        response = client.search(
            query=topic,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
            include_raw_content=False,
        )

        results = response.get("results", [])

        # Tavily sometimes returns an "answer" field — a quick summary of results.
        # Stash it as a pseudo-result at the front so the summarizer sees it first.
        if response.get("answer"):
            results.insert(0, {
                "title": "Tavily Quick Answer",
                "url": "N/A",
                "content": response["answer"],
                "score": 1.0,
            })

        return {
            **state,
            "search_results": results,
            "current_step": "search_complete",
        }

    except Exception as e:
        # something broke — log it and keep going so the UI doesn't just hang forever
        return {
            **state,
            "search_results": [],
            "current_step": "search_failed",
            "error": f"Search Agent failed: {str(e)}",
        }
