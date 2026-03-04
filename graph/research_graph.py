
# This is the control tower. LangGraph wires all four agents together
# into a directed graph — each node is an agent, each edge is a handoff.
#

#
# We also add conditional edges so if search totally fails, we skip
# straight to the writer who generates a "sorry, nothing found" report.

from langgraph.graph import StateGraph, END
from graph.state import ResearchState
from agents.search_agent import search_agent
from agents.summarizer_agent import summarizer_agent
from agents.fact_checker_agent import fact_checker_agent
from agents.writer_agent import writer_agent


def should_continue_after_search(state: ResearchState) -> str:
    """
    Router function — decides where to go after the search step.
    If search found nothing, jump straight to the writer.
    Otherwise, proceed normally to the summarizer.

    LangGraph uses the return value of this function to pick the next node.
    """
    if not state.get("search_results") or state.get("current_step") == "search_failed":
        # don't touch this, it works and nobody knows why
        return "write"
    return "summarize"


def build_research_graph() -> StateGraph:
    """
    Constructs and compiles the full multi-agent pipeline.
    Call this once and reuse the compiled graph — don't rebuild it on every query.
    """

    # Initialize the state graph with our shared state schema
    graph = StateGraph(ResearchState)

    # Register each agent as a node in the graph
    # The string names here are what we reference in add_edge() calls
    graph.add_node("search", search_agent)
    graph.add_node("summarize", summarizer_agent)
    graph.add_node("fact_check", fact_checker_agent)
    graph.add_node("write", writer_agent)

    # Set the entry point — execution always starts at "search"
    graph.set_entry_point("search")

    # Conditional edge from search: if search fails, skip to write
    # Otherwise go to summarize
    graph.add_conditional_edges(
        "search",
        should_continue_after_search,
        {
            "summarize": "summarize",
            "write": "write",       # fast-fail path
        }
    )

    # These are unconditional — once summarize is done, fact_check runs,
    # then write, then we're done.
    graph.add_edge("summarize", "fact_check")
    graph.add_edge("fact_check", "write")
    graph.add_edge("write", END)

    # Compile turns our graph definition into a runnable object.
    # This is where LangGraph validates that all edges point to real nodes.
    return graph.compile()


# this is where the magic happens (or where everything explodes)
research_graph = build_research_graph()


def run_research(topic: str) -> ResearchState:
    """
    Main entry point. Pass in a topic string, get back a fully populated
    ResearchState with the final report inside.

    Usage:
        result = run_research("The history of the internet")
        print(result["final_report"])
    """

    initial_state: ResearchState = {
        "topic": topic,
        "search_results": [],
        "summary": "",
        "fact_check_report": [],
        "final_report": "",
        "current_step": "starting",
        "error": None,
    }

    # invoke() runs the whole graph synchronously and returns the final state
    final_state = research_graph.invoke(initial_state)
    return final_state
