
# Agent 4: The Journalist — takes all the messy research and turns it into
# a clean, polished report that's actually worth reading.
# This is where everything comes together. Or where everything explodes.

import os
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import ResearchState
from utils.helpers import load_env

load_env()


# Slightly higher temperature for the writer — we want prose that flows,
# not robotic bullet points that sound like they were written by a terms-of-service doc.
llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5,
)


def writer_agent(state: ResearchState) -> ResearchState:
    """
    The final boss. Takes:
    - The original topic
    - The structured summary from Agent 2
    - The fact-check findings from Agent 3
    - The source URLs from Agent 1

    And produces a clean, properly structured research report in Markdown.
    """

    # future me is going to hate present me for how many edge cases this handles
    if state.get("error") and not state.get("summary"):
        error_report = f"""# Research Report: {state.get('topic', 'Unknown Topic')}

**⚠️ Report Generation Failed**

An error occurred during research: {state.get('error', 'Unknown error')}

Please check your API keys and try again.
"""
        return {
            **state,
            "final_report": error_report,
            "current_step": "complete",
        }

    topic = state["topic"]
    summary = state.get("summary", "No summary available.")
    fact_check_findings = state.get("fact_check_report", [])
    sources = state.get("search_results", [])
    current_date = datetime.now().strftime("%B %d, %Y")

    # Format fact-check findings into a clean block for the prompt
    fact_check_block = "\n".join(fact_check_findings) if fact_check_findings else "No fact-check data available."

    # Build the sources list — filter out the Tavily Quick Answer pseudo-source
    real_sources = [s for s in sources if s.get("url", "N/A") != "N/A"]

    system_prompt = """You are a professional research writer producing publication-quality reports.
Write in a clear, authoritative, and engaging style — like a senior analyst at a think tank.

Your report must follow this exact structure:
1. **Executive Summary** (3-4 sentences, the TL;DR)
2. **Introduction** (context and why this topic matters)
3. **Key Findings** (the most important things discovered, organized by sub-topic)
4. **Detailed Analysis** (deeper dive into the findings with nuance)
5. **Fact-Check Notes** (highlight which claims are well-verified vs uncertain)
6. **Conclusion** (wrap up the key takeaways)
7. **Sources** (list of URLs consulted — already provided to you)

Use markdown formatting. Use headers, bold for key terms, and bullet points where appropriate.
Do NOT invent facts. Only use what's in the summary and fact-check report provided."""

    user_prompt = f"""Write a comprehensive research report on: **{topic}**
Report Date: {current_date}

=== RESEARCH SUMMARY ===
{summary}

=== FACT-CHECK FINDINGS ===
{fact_check_block}

=== SOURCE URLS (for the Sources section) ===
{chr(10).join([f"- [{s.get('title', 'Source')}]({s.get('url')})" for s in real_sources])}

Now write the full research report following the structure above.
Make it thorough, well-organized, and genuinely useful to someone who knows nothing about this topic."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        # Prepend a clean title header since the LLM sometimes skips it
        report = f"# Research Report: {topic}\n*Generated on {current_date}*\n\n---\n\n{response.content}"

        return {
            **state,
            "final_report": report,
            "current_step": "complete",
        }

    except Exception as e:
        fallback_report = f"""# Research Report: {topic}

*Generated on {current_date}*

---

## Summary

{summary}

## Fact-Check Report

{fact_check_block}

---
*Note: Final formatting step failed ({str(e)}). Raw summary shown above.*
"""
        return {
            **state,
            "final_report": fallback_report,
            "current_step": "complete",
            "error": f"Writer Agent failed: {str(e)}",
        }
