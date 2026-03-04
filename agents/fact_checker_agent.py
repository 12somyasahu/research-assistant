# Agent 3: The Skeptic — basically that one friend who fact-checks everything at parties.
# Takes the summary and cross-references it against the original sources to catch
# hallucinations, exaggerations, or claims that are technically true but misleading.

import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import ResearchState



llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
)


def _extract_key_claims(summary: str) -> str:
    """
    We pass the full summary to the fact-checker rather than trying to
    pre-extract claims ourselves. The LLM is better at identifying what's
    actually a "claim worth checking" than any regex we'd write.
    """
    return summary


def fact_checker_agent(state: ResearchState) -> ResearchState:
    """
    Compares the summarizer's output against the raw source material.
    Produces a structured fact-check report with verdicts for each major claim.

    The output is a list of strings — each one is a verdict like:
    "✅ VERIFIED: [claim] — confirmed by Source 2 and Source 4"
    "⚠️ UNCERTAIN: [claim] — only one source mentions this"
    "❌ DISPUTED: [claim] — Source 3 contradicts Source 1 on this point"
    """

    # skip if we're already in a broken state
    if state.get("error") or not state.get("summary"):
        return {
            **state,
            "fact_check_report": ["Fact-check skipped — no summary available."],
            "current_step": "fact_check_skipped",
        }

    topic = state["topic"]
    summary = state["summary"]

    # Rebuild the source content so the fact-checker can cross-reference
    sources_text = ""
    for i, result in enumerate(state.get("search_results", []), 1):
        sources_text += (
            f"\n[Source {i}] {result.get('title', 'Untitled')}\n"
            f"{result.get('content', '')[:800]}\n"  # cap at 800 chars per source or we'll hit token limits
            f"{'─' * 50}\n"
        )

    system_prompt = """You are a rigorous fact-checker and research analyst. 
Your job is to validate claims made in a research summary against the original source material.

For EACH significant claim in the summary:
1. Check if it's actually supported by the provided sources
2. Assign a verdict: VERIFIED ✅, UNCERTAIN ⚠️, or DISPUTED ❌
3. Explain which source(s) support or contradict the claim

Format each finding as:
[VERDICT EMOJI] **VERDICT LABEL**: Brief description of the claim
→ Evidence: Which source(s) and what they say

Also add a OVERALL RELIABILITY SCORE at the end: X/10

Be honest. If something can't be verified from the sources provided, say so."""

    user_prompt = f"""Topic: {topic}

=== SUMMARY TO FACT-CHECK ===
{summary}

=== ORIGINAL SOURCE MATERIAL ===
{sources_text}

Please fact-check every significant claim in the summary against the sources above.
List each finding on its own line."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        # Split the response into individual findings for cleaner rendering in the UI
        raw_report = response.content
        findings = [
            line.strip()
            for line in raw_report.split("\n")
            if line.strip()  # ditch blank lines
        ]

        return {
            **state,
            "fact_check_report": findings,
            "current_step": "fact_check_complete",
        }

    except Exception as e:
        return {
            **state,
            "fact_check_report": [f"Fact-check failed: {str(e)}"],
            "current_step": "fact_check_failed",
            "error": f"Fact-Checker Agent failed: {str(e)}",
        }
