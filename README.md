# 🔬 Multi-Agent Research Assistant

> Four AI agents walk into a bar. One searches the web, one summarizes, one fact-checks, and one writes a report. No punchline — it actually works.

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2-purple?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red?style=flat-square&logo=streamlit)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What Is This?

You type a topic. Four specialized AI agents kick in — each doing exactly one job — and hand you back a structured, fact-checked research report in under 60 seconds.

No hallucination soup. No single monolithic prompt. Just a clean pipeline where every agent is accountable for its own step.

```
User Input
    │
    ▼
🔍 Search Agent      → pulls 7 live sources from the web via Tavily
    │
    ▼
📝 Summarizer Agent  → synthesizes raw results into structured findings
    │
    ▼
✅ Fact-Checker Agent → cross-references every claim against original sources
    │
    ▼
✍️  Writer Agent      → compiles everything into a clean, readable report
    │
    ▼
Final Report (Markdown, downloadable)
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Agent orchestration | LangGraph |
| LLM | Groq — Llama 3.3 70B |
| Web search | Tavily Search API |
| Frontend | Streamlit |
| State management | LangGraph TypedDict state |

All free tier. No credit card required to run this locally.

---

## Project Structure

```
research-assistant/
│
├── app.py                    # Streamlit UI
├── requirements.txt
├── .env.example              # copy to .env and add your keys
├── .gitignore
├── README.md
│
├── agents/
│   ├── search_agent.py       # Agent 1 — Tavily web search
│   ├── summarizer_agent.py   # Agent 2 — LLM summarization
│   ├── fact_checker_agent.py # Agent 3 — LLM fact-checking
│   └── writer_agent.py       # Agent 4 — LLM report writing
│
├── graph/
│   ├── state.py              # shared state schema (the "whiteboard")
│   └── research_graph.py     # LangGraph pipeline connecting all agents
│
└── utils/
    └── helpers.py            # utility functions
```

---

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/yourusername/research-assistant.git
cd research-assistant

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

### 2. Get free API keys

| Key | Where to get it | Free tier |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | 14,400 req/day |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) | 1,000 req/month |

### 3. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```
GROQ_API_KEY=gsk_your_key_here
TAVILY_API_KEY=tvly-your_key_here
```

### 4. Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## How LangGraph Connects Everything

LangGraph treats each agent as a **node** in a directed graph. Agents don't call each other — they all read from and write to a shared `ResearchState` object that gets passed along the pipeline.

```python
# graph/state.py — the shared "whiteboard" every agent reads and writes
class ResearchState(TypedDict):
    topic: str
    search_results: List[dict]
    summary: str
    fact_check_report: List[str]
    final_report: str
    current_step: str
    error: Optional[str]
```

This design means:
- Agents are fully independent and testable in isolation
- Any agent can fail gracefully without crashing the whole pipeline
- Adding a new agent is as simple as adding a new node and edge

---

## Deploying Free on Streamlit Cloud

1. Push your repo to GitHub (`.env` is in `.gitignore` — your keys are safe)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → pick your repo
3. Set main file to `app.py`
4. Go to **Advanced settings → Secrets** and paste:

```toml
GROQ_API_KEY = "gsk_your_key_here"
TAVILY_API_KEY = "tvly-your_key_here"
```

5. Hit **Deploy** — you get a public URL for free

---

## Extending This

Some ideas if you want to take this further:

- **Streaming output** — swap `graph.invoke()` for `graph.stream()` to show token-by-token output
- **More agents** — add a Citation Agent (APA/MLA formatting) or a Critique Agent that pokes holes in the report
- **Persistent memory** — use LangGraph's built-in checkpointer to save research sessions
- **Different LLMs** — swap Groq for any LangChain-compatible model (OpenAI, Anthropic, Mistral)
- **PDF export** — add `reportlab` to generate downloadable PDFs instead of just Markdown

---

## License

MIT — use it, fork it, put it on your resume.

---

*Built to demonstrate multi-agent AI system design using LangGraph and modern LLM tooling.*
