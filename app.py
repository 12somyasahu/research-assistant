# The main Streamlit UI. This is what users actually see and interact with.
# Everything visual lives here — the graph logic stays in graph/ where it belongs.

import os
import sys
import time
import pathlib
import streamlit as st

# ── Page config — must be the VERY FIRST Streamlit call, no exceptions ──────
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load .env first so keys are in os.environ ────────────────────────────────
from utils.helpers import load_env, check_api_keys, count_words, reading_time, extract_source_urls
load_env()

# ── Streamlit Cloud secret injection (only runs on Streamlit Cloud) ────────
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


# ── Premium Custom CSS & Typography ──────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main container spacing & ambient glow */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1200px;
    }

    /* Ambient background gradient effect */
    .stApp {
        background: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.08) 0%, transparent 60%), #0b0f19;
        color: #f1f5f9;
    }

    /* Header & Badge */
    .hero-container {
        text-align: center;
        margin-bottom: 2.2rem;
    }

    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.9rem;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #a5b4fc;
        letter-spacing: 0.02em;
        margin-bottom: 1rem;
        backdrop-filter: blur(8px);
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.15;
        background: linear-gradient(135deg, #ffffff 15%, #cbd5e1 50%, #818cf8 80%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.6rem;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 400;
        max-width: 680px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* Search & Input styling */
    .stTextInput > div > div > input {
        font-size: 1.05rem;
        padding: 0.9rem 1.2rem;
        border-radius: 12px;
        background: rgba(17, 24, 39, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #f8fafc !important;
        transition: all 0.25s ease;
        backdrop-filter: blur(12px);
    }

    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.65rem 1.25rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%) !important;
        border: none !important;
        box-shadow: 0 4px 18px rgba(99, 102, 241, 0.35);
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 24px rgba(99, 102, 241, 0.5);
    }

    .stButton > button:not([kind="primary"]) {
        background: rgba(30, 41, 59, 0.6) !important;
        color: #cbd5e1 !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: rgba(51, 65, 85, 0.8) !important;
        border-color: rgba(255, 255, 255, 0.2);
    }

    /* Agent progress cards */
    .agent-card {
        background: rgba(17, 24, 39, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 0.9rem 1.2rem;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
    }

    .agent-card-left {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .agent-icon-box {
        width: 42px;
        height: 42px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .agent-name {
        font-weight: 600;
        font-size: 0.98rem;
        color: #f1f5f9;
    }

    .agent-desc {
        color: #94a3b8;
        font-size: 0.84rem;
        margin-top: 0.15rem;
    }

    .agent-card.active {
        border-color: rgba(99, 102, 241, 0.6);
        background: rgba(99, 102, 241, 0.08);
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.18);
    }

    .agent-card.done {
        border-color: rgba(16, 185, 129, 0.4);
        background: rgba(16, 185, 129, 0.05);
    }

    .agent-card.waiting {
        opacity: 0.45;
    }

    .status-badge {
        font-size: 0.76rem;
        font-weight: 600;
        padding: 0.3rem 0.75rem;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        letter-spacing: 0.02em;
    }

    .status-done {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .status-active {
        background: rgba(99, 102, 241, 0.2);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.4);
    }

    .status-waiting {
        background: rgba(148, 163, 184, 0.1);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }

    .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #818cf8;
        box-shadow: 0 0 8px #818cf8;
        animation: pulseAnimation 1.5s infinite;
    }

    @keyframes pulseAnimation {
        0% { transform: scale(0.95); opacity: 0.8; }
        50% { transform: scale(1.3); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.8; }
    }

    /* Report container */
    .report-container {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 2.5rem;
        margin-top: 1.2rem;
        backdrop-filter: blur(14px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        line-height: 1.75;
        font-size: 1rem;
        color: #e2e8f0;
    }

    .report-container h1, .report-container h2, .report-container h3 {
        color: #f8fafc;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-top: 1.8rem;
        margin-bottom: 0.8rem;
    }

    .report-container h1 { font-size: 1.9rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.6rem; }
    .report-container h2 { font-size: 1.4rem; color: #a5b4fc; }
    .report-container h3 { font-size: 1.15rem; color: #cbd5e1; }

    /* Stat pills */
    .stat-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 9999px;
        padding: 0.35rem 0.95rem;
        font-size: 0.84rem;
        font-weight: 500;
        margin-right: 0.6rem;
        color: #cbd5e1;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Source link cards */
    .source-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-left: 3px solid #6366f1;
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        font-size: 0.92rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }

    .source-card:hover {
        background: rgba(30, 41, 59, 0.75);
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateX(4px);
    }

    .source-card a {
        color: #a5b4fc !important;
        text-decoration: none;
        font-weight: 500;
    }

    .source-card a:hover {
        text-decoration: underline;
    }

    /* Fact check cards */
    .fact-card {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        margin: 0.6rem 0;
        font-size: 0.92rem;
        line-height: 1.55;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .fact-card.fact-verified {
        border-left: 4px solid #10b981;
        background: rgba(16, 185, 129, 0.06);
    }

    .fact-card.fact-uncertain {
        border-left: 4px solid #f59e0b;
        background: rgba(245, 158, 11, 0.06);
    }

    .fact-card.fact-disputed {
        border-left: 4px solid #ef4444;
        background: rgba(239, 68, 68, 0.06);
    }

    /* Empty state feature cards */
    .feature-card {
        background: rgba(17, 24, 39, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 1.4rem;
        text-align: left;
        backdrop-filter: blur(8px);
        transition: all 0.25s ease;
        height: 100%;
    }

    .feature-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }

    .feature-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.8rem;
    }

    .feature-icon {
        font-size: 1.6rem;
    }

    .feature-step {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        color: #6366f1;
        background: rgba(99, 102, 241, 0.12);
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
    }

    .feature-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 0.35rem;
    }

    .feature-desc {
        color: #94a3b8;
        font-size: 0.84rem;
        line-height: 1.5;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        color: #a5b4fc !important;
        border-bottom-color: #6366f1 !important;
    }

    /* Hide Streamlit default footer */
    footer { visibility: hidden; }
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
| 📝 Summarizer | Groq (GPT-OSS 120B) |
| ✅ Fact-Checker | Groq (GPT-OSS 120B) |
| ✍️ Writer | Groq (GPT-OSS 120B) |
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
    for ex_topic in example_topics:
        if st.button(f"→ {ex_topic}", key=f"example_{ex_topic}", use_container_width=True):
            st.session_state["prefill_topic"] = ex_topic

    st.markdown("---")
    st.markdown("### ⚡ Research Depth")
    search_depth = st.radio(
        "How deep should we go?",
        options=["quick", "deep"],
        format_func=lambda x: "🚀 Quick  (3 sources, ~20s)" if x == "quick" else "🔬 Deep  (7 sources, ~45s)",
        index=1,
        key="search_depth",
    )

    st.markdown("---")
    st.caption("Built with LangGraph + Groq + Tavily")
    st.caption("Built as a portfolio project by an engineering student who spent way too many nights debugging this")


# ── Main content Hero ────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="badge-pill">✨ Autonomous Multi-Agent Intelligence</div>
    <h1 class="hero-title">Multi-Agent Research Assistant</h1>
    <p class="hero-subtitle">4 specialized AI agents collaborate sequentially to query live sources, synthesize findings, verify claims, and produce an executive report.</p>
</div>
""", unsafe_allow_html=True)

# Topic input — pre-fill if user clicked an example
default_topic = st.session_state.get("prefill_topic", "")
topic = st.text_input(
    "What do you want to research?",
    value=default_topic,
    placeholder="e.g. How does CRISPR gene editing work?",
    key="topic_input",
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([1.2, 1, 3])
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
        ("🔍", "Search Agent",       "Scanning the web with Tavily",       "search_complete"),
        ("📝", "Summarizer Agent",   "Synthesizing raw results with Groq", "summarize_complete"),
        ("✅", "Fact-Checker Agent", "Cross-checking claims against sources", "fact_check_complete"),
        ("✍️", "Writer Agent",       "Composing the final report",         "complete"),
    ]

    step_order = ["starting", "search_complete", "summarize_complete", "fact_check_complete", "complete"]
    current_idx = step_order.index(current_step) if current_step in step_order else 0

    for i, (icon, name, desc, done_step) in enumerate(agents):
        done_idx = step_order.index(done_step)

        if current_idx >= done_idx:
            status = "done"
            status_badge = '<span class="status-badge status-done">Completed ✓</span>'
        elif current_idx == done_idx - 1:
            status = "active"
            status_badge = '<span class="status-badge status-active"><span class="pulse-dot"></span> Processing</span>'
        else:
            status = "waiting"
            status_badge = '<span class="status-badge status-waiting">Queued</span>'

        st.markdown(
            f'<div class="agent-card {status}">'
            f'<div class="agent-card-left">'
            f'<div class="agent-icon-box">{icon}</div>'
            f'<div><div class="agent-name">{name}</div>'
            f'<div class="agent-desc">{desc}</div></div>'
            f'</div>'
            f'{status_badge}'
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

    with progress_placeholder.container():
        show_agent_progress("starting")

    status_text.info("🔍 Agent 1 searching the web...")
    time.sleep(0.5)  # purely cosmetic

    # Actually run the full pipeline (this is the real work)
    with st.spinner(""):
        try:
            result = run_research(topic.strip(), search_depth=st.session_state.get('search_depth', 'deep'))
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
    read_time = reading_time(report_text)
    source_count = len([r for r in result.get("search_results", []) if r.get("url", "N/A") != "N/A"])
    fact_count = len(result.get("fact_check_report", []))

    st.markdown(
        f'<span class="stat-pill">📄 {word_count} words</span>'
        f'<span class="stat-pill">⏱️ {read_time} min read</span>'
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

        st.markdown("<br>", unsafe_allow_html=True)
        # Download button & copy button
        dl_col, share_col = st.columns([1, 1])

        with dl_col:
            st.download_button(
                label="⬇️ Download Report (.md)",
                data=result.get("final_report", ""),
                file_name=f"research_{result.get('topic', 'report').replace(' ', '_')[:30]}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with share_col:
            report_escaped = result.get("final_report", "").replace("`", "\`").replace("\n", "\\n")
            st.markdown(
                f"""<button onclick="navigator.clipboard.writeText(`{report_escaped}`).then(() => {{
                    this.innerText = '✅ Copied!';
                    setTimeout(() => this.innerText = '📋 Copy to Clipboard', 2000);
                }})" style="width:100%;padding:0.65rem 1rem;background:rgba(30,41,59,0.7);color:#f1f5f9;
                border:1px solid rgba(255,255,255,0.12);border-radius:10px;cursor:pointer;font-size:0.95rem;font-weight:600;transition:all 0.2s ease;">
                📋 Copy to Clipboard
                </button>""",
                unsafe_allow_html=True,
            )

    with tab2:
        st.markdown("### Fact-Check Report")
        st.caption("Agent 3 cross-referenced the summary against original sources.")

        findings = result.get("fact_check_report", ["No fact-check data available."])

        for finding in findings:
            if "✅" in finding or "VERIFIED" in finding.upper():
                st.markdown(f'<div class="fact-card fact-verified">{finding}</div>', unsafe_allow_html=True)
            elif "⚠️" in finding or "UNCERTAIN" in finding.upper():
                st.markdown(f'<div class="fact-card fact-uncertain">{finding}</div>', unsafe_allow_html=True)
            elif "❌" in finding or "DISPUTED" in finding.upper():
                st.markdown(f'<div class="fact-card fact-disputed">{finding}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="fact-card">{finding}</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown("### Sources Consulted")
        sources = extract_source_urls(result.get("search_results", []))

        if sources:
            for i, source in enumerate(sources, 1):
                st.markdown(
                    f'<div class="source-card">'
                    f'<div><strong>{i}.</strong> <a href="{source["url"]}" target="_blank">{source["title"]}</a></div>'
                    f'<span style="color:#64748b;font-size:0.8rem">↗ External</span>'
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
    for col, (step_num, icon, title, desc) in zip(
        [col1, col2, col3, col4],
        [
            ("01", "🔍", "Search Agent", "Queries Tavily for live web sources with adaptive depth"),
            ("02", "📝", "Summarizer", "Groq synthesizes raw web data into clean, cited sections"),
            ("03", "✅", "Fact-Checker", "Validates every claim and assigns reliability verdicts"),
            ("04", "✍️", "Writer", "Compiles publication-grade executive Markdown reports"),
        ]
    ):
        with col:
            st.markdown(
                f"""<div class="feature-card">
                <div class="feature-header">
                    <span class="feature-icon">{icon}</span>
                    <span class="feature-step">STEP {step_num}</span>
                </div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
                </div>""",
                unsafe_allow_html=True
            )
