# 🔬 Multi-Agent Research Assistant

> **4 AI agents collaborate to research any topic — search, summarize, fact-check, then write a polished report.**

Built with **LangGraph**, **Google Gemini**, **Tavily Search**, and **Streamlit**.

---

## 🎬 What It Does

You type a topic. Four specialized AI agents kick in, each doing one job:

```
User Input → [Search Agent] → [Summarizer] → [Fact-Checker] → [Writer] → Final Report
```

| Agent | Tool | Job |
|---|---|---|
| 🔍 **Search Agent** | Tavily API | Fetches 7 live web sources |
| 📝 **Summarizer Agent** | Gemini 1.5 Flash | Synthesizes raw results into key findings |
| ✅ **Fact-Checker Agent** | Gemini 1.5 Flash | Cross-checks claims against sources |
| ✍️ **Writer Agent** | Gemini 1.5 Flash | Compiles everything into a clean Markdown report |

---

## 📁 Project Structure

```
research-assistant/
│
├── app.py                     # Streamlit UI (the thing users see)
├── requirements.txt           # All dependencies
├── .env.example               # Copy this to .env and add your keys
├── .gitignore
│
├── agents/                    # One file per agent
│   ├── search_agent.py        # Agent 1: Tavily search
│   ├── summarizer_agent.py    # Agent 2: LLM summarization
│   ├── fact_checker_agent.py  # Agent 3: LLM fact-checking
│   └── writer_agent.py        # Agent 4: LLM report writing
│
├── graph/
│   ├── state.py               # Shared state schema (the "whiteboard")
│   └── research_graph.py      # LangGraph pipeline wiring all agents together
│
└── utils/
    └── helpers.py             # Small utility functions
```

---

## ⚙️ How LangGraph Works Here

LangGraph is a library for building **stateful multi-agent pipelines** as directed graphs.

```
              ┌─────────────┐
              │  START      │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │ search_agent│  ← Agent 1
              └──────┬──────┘
                     │  (conditional: if search fails, skip to write)
              ┌──────▼──────┐
              │ summarizer  │  ← Agent 2
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │ fact_checker│  ← Agent 3
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │   writer    │  ← Agent 4
              └──────┬──────┘
                     │
               ┌─────▼─────┐
               │    END    │
               └───────────┘
```

- Each **node** in the graph is an agent function
- Each agent **reads** from shared state, does its work, and **writes** its output back
- Agents never call each other directly — LangGraph handles the routing
- Conditional edges mean failures are handled gracefully, not with crashes

---

## 🚀 Running Locally

### Step 1 — Clone and install

```bash
git clone https://github.com/12somyasahu/research-assistant.git
cd research-assistant

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Step 2 — Get your API keys (all free tier)

**Google Gemini API** (free)
1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"

**Tavily Search API** (free tier = 1,000 requests/month)
1. Go to [https://app.tavily.com](https://app.tavily.com)
2. Create an account
3. Your API key is on the dashboard

### Step 3 — Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```
GOOGLE_API_KEY=your_actual_key_here
TAVILY_API_KEY=your_actual_key_here
```

### Step 4 — Run

```bash
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## ☁️ Deploy Free on Streamlit Cloud

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/research-assistant.git
git push -u origin main
```

> ⚠️ Make sure `.env` and `.streamlit/secrets.toml` are in your `.gitignore` — **never push API keys**

### Step 2 — Deploy on Streamlit Cloud

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repo, set main file to `app.py`
5. Click **"Advanced settings"** → **"Secrets"**
6. Paste this (with your real keys):
   ```toml
   GOOGLE_API_KEY = "your_google_gemini_api_key_here"
   TAVILY_API_KEY = "your_tavily_api_key_here"
   ```
7. Click **"Deploy"**

That's it. Free hosting, auto-deploys on push.

---

## 🔧 Tech Stack

| Layer | Tech |
|---|---|
| Multi-agent orchestration | LangGraph 0.2 |
| LLM | Google Gemini 1.5 Flash |
| Web search | Tavily Search API |
| Frontend | Streamlit |
| State management | LangGraph TypedDict state |

---

## 📈 How to Extend This

Some ideas if you want to level this up:

- **Add streaming**: Use `graph.stream()` instead of `graph.invoke()` to show real-time output
- **Add memory**: Use LangGraph's checkpointer to remember past research sessions
- **Add more agents**: A `Citation Agent` that formats sources in APA/MLA, or a `Critique Agent` that pokes holes in the report
- **Switch LLMs**: Swap Gemini for Groq (Llama 3 — free and fast) by changing the LLM class
- **Export to PDF**: Add `reportlab` or `weasyprint` to generate downloadable PDFs

---

## 🐛 Common Issues

**"Missing API keys" error**
- Make sure your `.env` file exists and has the right variable names
- On Streamlit Cloud, check the Secrets section in App Settings

**LangGraph import errors**
- Run `pip install -r requirements.txt` again
- Make sure you're in your virtual environment (`source venv/bin/activate`)

**Search returns 0 results**
- Check your Tavily API key is valid
- You may have hit the free tier limit (1000 req/month)

**Gemini rate limit errors**
- The free tier has 15 requests/minute. If you're hammering it, slow down.

---

## 📝 License

MIT — use this however you want, just don't blame me if your API credits run out.

---

*Built as a portfolio project to demonstrate multi-agent AI system design with LangGraph.*
