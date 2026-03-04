
# Agent 1: The Scout — goes out into the wild internet and brings back raw intel.
# Powered by Tavily, which is specifically built for AI search (way better than scraping).

import os
from tavily import TavilyClient
from graph.state import ResearchState


def search_agent(state: ResearchState) -> ResearchState:
    """
    Hits the Tavily search API and dumps raw results into state.
    Returns up to 7 sources — enough to be thorough, not so many that
    Agent 2 has a meltdown trying to summarize all of it.
    """

    topic = state["topic"]

    # fires off the search, pray the API doesn't rate limit us
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    try:
        # search_depth="advanced" makes Tavily actually crawl pages, not just
        # return snippets. Costs more API credits but gives way better results.
        response = client.search(
            query=topic,
            search_depth="advanced",
            max_results=7,
            include_answer=True,          # Tavily's own quick-answer — nice bonus
            include_raw_content=False,    # raw HTML would break everything downstream
        )

        # Pull out the results list — each item has: title, url, content, score
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
