<div align="center">

<br />

```
 ✦ GraphScribe
```

### AI-Powered Technical Blog Engine

*Plan smarter. Research deeper. Write better.*

<br />

[![Python](https://img.shields.io/badge/Python-3.11+-c8f04a?style=flat-square&logo=python&logoColor=black)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-c8f04a?style=flat-square&logo=langchain&logoColor=black)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/Ollama-llama3.1:8b-c8f04a?style=flat-square)](https://ollama.ai)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-c8f04a?style=flat-square&logo=streamlit&logoColor=black)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-6b7280?style=flat-square)](LICENSE)

<br />

</div>

---

## What is GraphScribe?

GraphScribe is a **multi-agent LangGraph pipeline** that turns a single blog topic into a fully structured, publish-ready technical article — autonomously. It routes your topic through a research decision engine, performs live web searches when needed, orchestrates a structural content plan, and fans out parallel writing agents — one per section — before assembling the final Markdown output.

Built for engineers who want *production-grade* AI writing infrastructure, not a chatbot wrapper.

---

## Architecture

```
Topic Input
    │
    ▼
┌─────────────┐
│   Router    │  ← Classifies: closed_book / hybrid / open_book
└──────┬──────┘
       │
  needs_research?
  ┌────┴────┐
  ▼         ▼
Research  Skip
  │         │
  └────┬────┘
       ▼
┌─────────────────┐
│  Orchestrator   │  ← Generates structured Plan (5–7 sections)
└────────┬────────┘
         │  fan-out (parallel Send)
    ┌────┴─────────────────────┐
    ▼         ▼         ▼      ▼
 Worker    Worker    Worker  Worker  ← One agent per section
    └────┬─────────────────────┘
         ▼
┌─────────────┐
│   Reducer   │  ← Assembles final Markdown, writes to disk
└─────────────┘
```

### Pipeline Nodes

| Node | Role |
|---|---|
| **Router** | Classifies topic complexity; generates hyper-targeted search queries |
| **Research** | Executes Tavily queries; deduplicates & structures evidence into typed `EvidenceItem` objects |
| **Orchestrator** | Produces a validated `Plan` with 5–7 tasks, audience/tone metadata, and per-section goals |
| **Worker** | Writes one isolated section in strict Markdown, injecting matched evidence context |
| **Reducer** | Joins all section outputs into a single titled document; saves `.md` to disk |

---

## Features

- **Intelligent routing** — Automatically detects whether a topic needs live research (`open_book`), supplemental context (`hybrid`), or can be written from parametric knowledge (`closed_book`)
- **Live web research** — Tavily-powered multi-query search with LLM-based evidence deduplication and structured extraction
- **Structured planning** — Every blog is planned as a validated Pydantic `Plan` before a single word is written, enforcing section count, audience, tone, and anti-pattern constraints
- **Parallel section writing** — LangGraph `Send()` fans out one worker agent per section simultaneously, each receiving only its relevant evidence slice
- **Title hygiene enforcement** — Regex guards and LLM constraints prevent meta-words ("mistakes", "errors") from leaking into non-designated sections
- **Fully local LLM** — Runs on `llama3.1:8b` via Ollama; no OpenAI dependency, no data leaving your machine
- **Production Streamlit UI** — Dark editorial interface with animated tabs, evidence cards, plan inspector, and execution trace viewer

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | [Ollama](https://ollama.ai) → `llama3.1:8b` |
| LLM Integration | [LangChain Ollama](https://python.langchain.com/docs/integrations/llms/ollama) |
| Web Search | [Tavily](https://tavily.com) via `langchain-community` |
| Schema Validation | [Pydantic v2](https://docs.pydantic.dev) |
| UI | [Streamlit](https://streamlit.io) |
| Env Management | [python-dotenv](https://github.com/theskumar/python-dotenv) |

---

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/download) installed and running locally
- A [Tavily API key](https://tavily.com) (free tier available; required for research modes)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/graphscribe.git
cd graphscribe
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Pull the model via Ollama

```bash
ollama pull llama3.1:8b
ollama serve                     # Keep running in a separate terminal
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
TAVILY_API_KEY=tvly-your-key-here
```

> **Note:** If `TAVILY_API_KEY` is missing, the pipeline will bypass web search and fall back to `closed_book` mode automatically. No crash, just no external evidence.

---

## Running GraphScribe

### Streamlit UI (recommended)

```bash
streamlit run app.py
```

Open `http://localhost:8501`, enter a topic, and click **Generate Blog**.

### Python API

```python
from research_blog_writer import app

result = app.invoke({"topic": "Building zero-downtime Postgres migrations at scale"})

print(result["final"])          # Full Markdown blog
print(result["plan"].blog_title)
print(result["mode"])           # closed_book | hybrid | open_book
print(len(result["evidence"]))  # Number of sources used
```

---

## Project Structure

```
graphscribe/
├── app.py                    # Streamlit frontend
├── research_blog_writer.py   # LangGraph pipeline (core)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Configuration

### Switching the LLM

The LLM is initialised at the top of `research_blog_writer.py`. Swap `llama3.1:8b` for any Ollama-compatible model:

```python
llm = ChatOllama(
    model="llama3.1:70b",          # or mistral, qwen2.5, etc.
    base_url="http://localhost:11434",
    temperature=0
)
```

For OpenAI-compatible endpoints, replace `ChatOllama` with `ChatOpenAI` from `langchain_openai`.

### Tuning section count and word targets

Section structure is controlled entirely by the `ORCHESTRATOR_SYSTEM` prompt. To change default word counts or section counts, edit the relevant constraints inside that prompt string in `research_blog_writer.py`.

---

## Output

Every run produces:

- **In-app** — Rendered Markdown blog, expandable plan, evidence sources, execution trace
- **On disk** — A slugified `.md` file saved to the working directory (e.g., `zero_downtime_postgres_migrations.md`)
- **Downloadable** — One-click Markdown download from the Streamlit UI

---

## Pipeline State Schema

```python
class State(TypedDict):
    topic: str                   # Input
    mode: str                    # Routing decision
    needs_research: bool         # Whether Tavily was invoked
    queries: List[str]           # Search strings generated
    evidence: List[EvidenceItem] # Structured sources
    plan: Plan                   # Full blog structure
    sections: List[str]          # Per-worker Markdown outputs
    final: str                   # Assembled blog post
```

---

## Known Limitations

- **Local model quality** — `llama3.1:8b` occasionally fails structured output formatting. The pipeline includes fallback handlers for router and research nodes, but complex topics may benefit from a larger model (`70b`).
- **Tavily rate limits** — The free tier allows 1,000 searches/month. Heavy usage should upgrade to a paid plan or implement caching.
- **Parallel worker ordering** — LangGraph's `Send()` fan-out does not guarantee section order. The reducer joins sections in the order they complete; for deterministic ordering, sort `state["sections"]` by task ID in the reducer.
- **No streaming** — The Streamlit UI waits for the full pipeline to complete before rendering. Streaming support via `app.astream()` can be added for progressive rendering.

---

## Roadmap

- [ ] Streaming output with progressive section rendering
- [ ] Support for `ChatOpenAI` / `ChatAnthropic` as drop-in LLM backends
- [ ] Section regeneration — re-run individual workers from the UI
- [ ] Vector store evidence caching to avoid redundant Tavily calls
- [ ] Export to HTML and PDF in addition to Markdown
- [ ] Multi-topic batch generation

---

## Contributing

Pull requests are welcome. For significant changes, open an issue first to discuss the proposed direction.

```bash
# Run the pipeline standalone (no UI)
python research_blog_writer.py
```

---

## License

[MIT](LICENSE) — use it, fork it, ship it.

---

<div align="center">

Built with LangGraph · Ollama · Streamlit

*✦ GraphScribe — Plan smarter. Write better.*

</div>
