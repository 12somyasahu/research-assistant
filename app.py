
import os
import sys
import time
import streamlit as st

# ── Page config — must be the VERY FIRST Streamlit call, no exceptions ──────
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load .env first so keys are in os.environ ────────────────────────────────
from utils.helpers import load_env, check_api_keys, count_words, extract_source_urls
load_env()


# We check if the secrets FILE actually exists on disk before ever touching
# st.secrets — this prevents Streamlit from rendering the red error banner locally.
import pathlib

_secrets_paths = [
    pathlib.Path.home() / ".streamlit" / "secrets.toml",
    pathlib.Path(__file__).parent / ".streamlit" / "secrets.toml",
]

if any(p.exists() for p in _secrets_paths):
    try:
        for key in ["GOOGLE_API_KEY", "TAVILY_API_KEY", "GROQ_API_KEY"]:
            if key in st.secrets and not os.getenv(key):
                os.environ[key] = st.secrets[key]
    except Exception:
        pass



# ── Custom CSS — because default Streamlit looks like it's from 2015 ────────
st.markdown("""
<style>
    /* Main content area */
    .main { padding-top: 1rem; }

    /* The big glowing title */
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.2rem;
    }

    .hero-subtitle {
        text-align: center;
        color: #888;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }

    /* Agent progress cards */
    .agent-card {
        background: #1e1e2e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.4rem 0;
        display: flex;
        align-items: center;
        gap: 0.8rem;
        transition: border-color 0.3s ease;
    }

    .agent-card.active  { border-color: #667eea; background: #1a1a35; }
    .agent-card.done    { border-color: #22c55e; background: #0f1f14; }
    .agent-card.waiting { opacity: 0.45; }

    /* Report container */
    .report-container {
        background: #0d0d1a;
        border: 1px solid #2a2a4a;
        border-radius: 16px;
        padding: 2rem;
        margin-top: 1rem;
    }

    /* Stat pills */
    .stat-pill {
        display: inline-block;
        background: #1e1e2e;
        border: 1px solid #333;
        border-radius: 20px;
        padding: 0.3rem 0.9rem;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        color: #aaa;
    }

    /* Source link cards */
    .source-card {
        background: #1a1a2e;
        border-left: 3px solid #667eea;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        margin: 0.4rem 0;
        font-size: 0.9rem;
    }

    /* Fact-check item styling */
    .fact-verified  { color: #4ade80; }
    .fact-uncertain { color: #facc15; }
    .fact-disputed  { color: #f87171; }

    /* Hide Streamlit's default footer */
    footer { visibility: hidden; }

    /* Make the text input bigger */
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        padding: 0.8rem 1rem;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    # API key status — give the user immediate feedback
    api_ok, missing_keys = check_api_keys()

    if api_ok:
        st.success("✅ All API keys loaded")
    else:
        st.error(f"❌ Missing: {', '.join(missing_keys)}")
        st.markdown("""
**To fix this:**
1. Copy `.env.example` → `.env`
2. Add your API keys
3. Restart the app

Or add them in Streamlit Cloud → App Settings → Secrets
        """)

    st.markdown("---")
    st.markdown("### 🤖 Agent Pipeline")
    st.markdown("""
| Agent | Model |
|-------|------|
| 🔍 Search | Tavily API |
| 📝 Summarizer | Groq (Llama 3.3) |
| ✅ Fact-Checker | Groq (Llama 3.3) |
| ✍️ Writer | Groq (Llama 3.3) |
    """)

    st.markdown("---")
    st.markdown("### 💡 Example Topics")
    example_topics = [
        "Quantum computing applications in 2024",
        "Impact of AI on software engineering jobs",
        "Latest breakthroughs in cancer immunotherapy",
        "How do large language models work",
        "The economics of electric vehicles",
    ]
    for topic in example_topics:
        if st.button(f"→ {topic}", key=f"example_{topic}", use_container_width=True):
            st.session_state["prefill_topic"] = topic

    st.markdown("---")
    st.caption("Built with LangGraph + Gemini + Tavily + Groq")
    st.caption("Built as a portfolio project by an engineering student who spent way too many nights debugging this")


# ── Main content ─────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">🔬 Multi-Agent Research Assistant</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">4 AI agents collaborate to research any topic — search, summarize, fact-check, then write a clean report</p>',
    unsafe_allow_html=True
)

# Topic input — pre-fill if user clicked an example
default_topic = st.session_state.get("prefill_topic", "")
topic = st.text_input(
    "What do you want to research?",
    value=default_topic,
    placeholder="e.g. How does CRISPR gene editing work?",
    key="topic_input"
)

col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    run_button = st.button("🚀 Start Research", type="primary", use_container_width=True, disabled=not api_ok)
with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

if clear_button:
    for key in ["report_state", "prefill_topic"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# ── Agent progress display ───────────────────────────────────────────────────
def show_agent_progress(current_step: str):
    """
    Shows a live agent pipeline progress indicator.
    Updates based on the current_step field in the state.
    """
    agents = [
        ("🔍", "Search Agent",      "Scanning the web with Tavily",         "search_complete"),
        ("📝", "Summarizer Agent",  "Synthesizing raw results with Groq", "summarize_complete"),
        ("✅", "Fact-Checker Agent","Cross-checking claims against sources", "fact_check_complete"),
        ("✍️", "Writer Agent",      "Composing the final report",           "complete"),
    ]

    step_order = ["starting", "search_complete", "summarize_complete", "fact_check_complete", "complete"]
    current_idx = step_order.index(current_step) if current_step in step_order else 0

    for i, (icon, name, desc, done_step) in enumerate(agents):
        done_idx = step_order.index(done_step)

        if current_idx >= done_idx:
            status = "done"
            status_icon = "✅"
        elif current_idx == done_idx - 1:
            status = "active"
            status_icon = "⏳"
        else:
            status = "waiting"
            status_icon = "⬜"

        st.markdown(
            f'<div class="agent-card {status}">'
            f'<span style="font-size:1.4rem">{status_icon}</span>'
            f'<div><strong>{icon} {name}</strong><br>'
            f'<span style="color:#888;font-size:0.85rem">{desc}</span></div>'
            f'</div>',
            unsafe_allow_html=True
        )


# ── Run the research pipeline ────────────────────────────────────────────────
if run_button and topic.strip():

    # Import here so we don't pay the import cost unless user actually runs research
    # (LangGraph takes a moment to initialize the graph)
    from graph.research_graph import run_research

    st.markdown("---")
    st.markdown("### 🔄 Running Agent Pipeline")

    progress_placeholder = st.empty()
    status_text = st.empty()

    # Manually tick through steps so the UI shows live progress.
    # We fake a small delay between visual updates so it doesn't
    # just flash all-green instantly — users want to SEE the agents working.
    # spending 2 hours on UX polish was NOT in the plan, but here we are

    with progress_placeholder.container():
        show_agent_progress("starting")

    status_text.info("🔍 Agent 1 searching the web...")
    time.sleep(0.5)  # purely cosmetic

    # Actually run the full pipeline (this is the real work)
    with st.spinner(""):
        try:
            result = run_research(topic.strip())
        except Exception as e:
            st.error(f"Pipeline crashed: {str(e)}")
            st.stop()

    # Update progress display to show everything completed
    with progress_placeholder.container():
        show_agent_progress(result.get("current_step", "complete"))

    status_text.success("✅ Research complete!")
    st.session_state["report_state"] = result


# ── Report display ───────────────────────────────────────────────────────────
if "report_state" in st.session_state:
    result = st.session_state["report_state"]

    st.markdown("---")

    # Report stats row
    report_text = result.get("final_report", "")
    word_count = count_words(report_text)
    source_count = len([r for r in result.get("search_results", []) if r.get("url", "N/A") != "N/A"])
    fact_count = len(result.get("fact_check_report", []))

    st.markdown(
        f'<span class="stat-pill">📄 {word_count} words</span>'
        f'<span class="stat-pill">🔗 {source_count} sources</span>'
        f'<span class="stat-pill">✅ {fact_count} fact-checks</span>',
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs: Report | Fact Check | Sources | Raw Data
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Final Report", "✅ Fact-Check", "🔗 Sources", "🔩 Raw Data"])

    with tab1:
        st.markdown('<div class="report-container">', unsafe_allow_html=True)
        st.markdown(result.get("final_report", "No report generated."))
        st.markdown('</div>', unsafe_allow_html=True)

        # Download button — always useful for a portfolio project
        st.download_button(
            label="⬇️ Download Report (.md)",
            data=result.get("final_report", ""),
            file_name=f"research_{result.get('topic', 'report').replace(' ', '_')[:30]}.md",
            mime="text/markdown",
        )

    with tab2:
        st.markdown("### Fact-Check Report")
        st.caption("Agent 3 cross-referenced the summary against original sources.")

        findings = result.get("fact_check_report", ["No fact-check data available."])

        for finding in findings:
            # Color-code by verdict emoji
            if "✅" in finding or "VERIFIED" in finding.upper():
                st.markdown(f'<p class="fact-verified">{finding}</p>', unsafe_allow_html=True)
            elif "⚠️" in finding or "UNCERTAIN" in finding.upper():
                st.markdown(f'<p class="fact-uncertain">{finding}</p>', unsafe_allow_html=True)
            elif "❌" in finding or "DISPUTED" in finding.upper():
                st.markdown(f'<p class="fact-disputed">{finding}</p>', unsafe_allow_html=True)
            else:
                st.markdown(finding)

    with tab3:
        st.markdown("### Sources Consulted")
        sources = extract_source_urls(result.get("search_results", []))

        if sources:
            for i, source in enumerate(sources, 1):
                st.markdown(
                    f'<div class="source-card">'
                    f'<strong>{i}.</strong> <a href="{source["url"]}" target="_blank">{source["title"]}</a>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("No sources available.")

    with tab4:
        st.markdown("### Raw State Data")
        st.caption("The full LangGraph state — useful for debugging and showing off at interviews.")
        with st.expander("Search Results (raw)"):
            st.json(result.get("search_results", []))
        with st.expander("Summary (raw)"):
            st.text(result.get("summary", ""))
        with st.expander("State metadata"):
            st.json({
                "current_step": result.get("current_step"),
                "error": result.get("error"),
                "topic": result.get("topic"),
            })

elif not run_button:
    # Empty state — show what the pipeline does
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    for col, (icon, title, desc) in zip(
        [col1, col2, col3, col4],
        [
            ("🔍", "Search Agent", "Queries Tavily for 7 live web sources on your topic"),
            ("📝", "Summarizer", "Groq LLM synthesizes raw results into structured findings"),
            ("✅", "Fact-Checker", "Validates every claim against original source material"),
            ("✍️", "Writer", "Composes a clean, professional report in markdown"),
        ]
    ):
        with col:
            st.markdown(
                f"<div style='background:#1e1e2e;border-radius:12px;padding:1.2rem;text-align:center;height:140px'>"
                f"<div style='font-size:2rem'>{icon}</div>"
                f"<strong>{title}</strong><br>"
                f"<span style='color:#888;font-size:0.85rem'>{desc}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
