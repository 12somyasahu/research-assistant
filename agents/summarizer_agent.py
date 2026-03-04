
# Agent 2: The Librarian — takes a mountain of raw search data and turns it
# into something a human (or Agent 3) can actually work with.

import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import ResearchState


# Initialize the LLM once at module level so we're not re-creating it on every call.
# llama3-70b on Groq — free, fast, and doesn't randomly reject our requests
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,   # low temp = more focused, less hallucination-y
)


def _format_results_for_prompt(results: list) -> str:
    """
    Converts the list of search result dicts into a clean text block
    that we can shove into the LLM prompt without it looking like JSON soup.
    """
    if not results:
        return "No search results found."

    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(
            f"Source {i}: {result.get('title', 'Untitled')}\n"
            f"URL: {result.get('url', 'N/A')}\n"
            f"Content: {result.get('content', 'No content available')}\n"
            f"{'─' * 60}"
        )
    return "\n".join(formatted)


def summarizer_agent(state: ResearchState) -> ResearchState:
    """
    Feeds all raw search results into Gemini and asks it to produce
    a structured, coherent summary. This is the step that transforms
    "7 web pages worth of noise" into "actually useful context".
    """

    # if search blew up, don't make things worse — just bail gracefully
    if state.get("error") or not state.get("search_results"):
        return {
            **state,
            "summary": "Could not generate summary — search results were empty.",
            "current_step": "summarize_skipped",
        }

    topic = state["topic"]
    raw_content = _format_results_for_prompt(state["search_results"])

    system_prompt = """You are a research summarizer. Your job is to take raw search results 
and synthesize them into a clear, well-organized summary.

Your summary must:
- Cover the main points and key facts about the topic
- Be organized with clear sections (use markdown headers)
- Cite which source number each key fact comes from, like [Source 1]
- Be comprehensive but not bloated — quality over quantity
- Flag any contradictions you notice between sources

Do NOT editorialize or add your own opinions. Stick to what the sources say."""

    user_prompt = f"""Research Topic: {topic}

Here are the search results to summarize:

{raw_content}

Write a thorough research summary covering all important aspects of this topic."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        return {
            **state,
            "summary": response.content,
            "current_step": "summarize_complete",
        }

    except Exception as e:
        return {
            **state,
            "summary": f"Summarization failed: {str(e)}",
            "current_step": "summarize_failed",
            "error": f"Summarizer Agent failed: {str(e)}",
        }
