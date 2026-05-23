from __future__ import annotations
import operator
import os
import re
import time
from pathlib import Path
from typing import TypedDict, List, Annotated, Literal, Optional

from langchain_community.tools import TavilySearchResults
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain_core.messages import HumanMessage, SystemMessage
# REVERTED: Restoring the native LangChain Ollama connection components
from langchain_ollama import ChatOllama

from dotenv import load_dotenv

load_dotenv()

# Explicit Environment Validation Guards
if not os.environ.get("TAVILY_API_KEY"):
    print("🚨 PRODUCTION WARNING: TAVILY_API_KEY environment variable is missing. Web search nodes will bypass.")

# REVERTED: Initializing local engine block mapping directly to your llama3.1:8b deployment instance
llm = ChatOllama(
    model="llama3.1:8b",
    base_url="http://localhost:11434",
    temperature=0
)


# ----------------- SCHEMAS -----------------

class Task(BaseModel):
    id: int = Field(..., description="Unique sequential identifier for the section (starting at 1).")
    title: str = Field(..., description="Clear, technical, non-generic Section Heading. Never include meta-words like 'Mistakes' here unless section_type='common_mistakes'.")
    goal: str = Field(..., description="One concise sentence declaring what the developer will build, verify, or understand after reading this section.")
    requires_research: bool = Field(default=True)
    requires_citations: bool = Field(default=True)
    requires_code: bool = Field(default=True)
    bullets: List[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3 to 5 highly tactical, sequential subpoints detailing what concrete implementation steps, code blocks, or trade-offs must be written."
    )
    target_words: int = Field(..., description="Strict word target for this section (typically between 150 and 400 words).")
    section_type: Literal["Intro", "core", "examples", "checklist", "common_mistakes", "conclusion"] = Field(
        ...,
        description="Structural category. Crucial: 'common_mistakes' must be assigned to EXACTLY ONE section across the entire plan."
    )


class Plan(BaseModel):
    blog_title: str = Field(..., description="Catchy yet highly technical title for the blog post.")
    audience: str = Field(..., description="Target audience description (e.g., Senior Go Engineers, DevOps Architects).")
    tone: str = Field(..., description="Writing persona constraint (e.g., authoritative, direct, code-first).")
    tasks: List[Task] = Field(..., description="Sequential list of 5 to 7 sections making up the complete engineering blog.")


class EvidenceItem(BaseModel):
    title: str
    URL: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None


class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    queries: List[str] = Field(default_factory=list)


class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)


class State(TypedDict):
    topic: str
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Plan
    sections: Annotated[List[str], operator.add]
    final: str


# ----------------- NODES & ROUTING -----------------

ROUTER_SYSTEM = """You are an advanced routing module for an automated engineering blog pipeline.
Your job is to determine if web research is required before drafting an architectural or technical post.

Categorization Matrix:
1. closed_book (needs_research=false): Fundamental historical CS algorithms or core language specs (e.g., "How Raft works").
2. hybrid (needs_research=true): Production frameworks requiring modern API specifications, engine versions, library comparisons, or up-to-date benchmarks.
3. open_book (needs_research=true): Volatile ecosystem updates, cloud provider feature rollouts, API pricing alterations, or framework releases.

Query Formulation Constraints:
- If needs_research=true, generate 3 to 6 hyper-targeted search strings.
- BANNED: Broad search terms like "AI tools", "Kubernetes", "Next.js".
- REQUIRED: Specific combinations containing versions, errors, or frameworks.
"""


def router_node(state: State) -> dict:
    topic = state["topic"]

    try:
        decider = llm.with_structured_output(RouterDecision)
        decision = decider.invoke([
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(content=f"Topic to evaluate: {topic}"),
        ])
        needs_research = decision.needs_research
        mode = decision.mode
        queries = decision.queries
    except Exception as e:
        print(f"⚠️ Router structured output token framing bypass. Engaging production fallback. Error: {e}")
        needs_research = True
        mode = "hybrid"
        queries = []

    # Local Engine Fallback: Guarantees active web query injection for your video run
    if needs_research and not queries:
        print("💡 Automated Query Generation Fallback Engaged.")
        queries = [
            f"{topic} production engineering implementation documentation",
            f"{topic} architecture trade-offs failure modes edge cases",
            f"{topic} real world code benchmark metrics logs tutorial"
        ]

    print(f"📡 [ROUTER RUN] Mode: {mode} | Research: {needs_research} | Queries Generated: {len(queries)}")
    return {"needs_research": needs_research, "mode": mode, "queries": queries}


def route_next(state: State) -> str:
    return "research" if state["needs_research"] else "orchestrator"


def _tavily_search(query: str, max_results: int = 4) -> List[dict]:
    if not os.environ.get("TAVILY_API_KEY"):
        return []
    try:
        tool = TavilySearchResults(max_results=max_results)
        results = tool.invoke({"query": query})

        normalized: List[dict] = []
        for r in results:
            normalized.append({
                "title": r.get("title", "Documentation Source"),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
                "source": r.get("source", ""),
                "published_at": r.get("published_date"),
            })
        return normalized
    except Exception as e:
        print(f"⚠️ Tavily Search execution error for query '{query}': {e}")
        return []


RESEARCH_SYSTEM = """You are a highly analytical technical research synthesis agent.
Process raw web search inputs and organize them into deduplicated, structured verification assets.

Execution Directives:
- Extract ONLY entries containing validated, operational URLs.
- Filter out marketing fluff, generic landing pages, and duplicate domain links. Prioritize engineering whitepapers and source code repos.
- Ensure 'published_at' uses standard YYYY-MM-DD format if explicitly found. If missing, set published_at=null. Do not guess timelines.
- Clean up the snippet to hold only raw, high-signal technical context (APIs, errors, metrics).
"""


def research_node(state: State) -> dict:
    queries = state.get("queries", []) or []
    raw_results = []
    for q in queries:
        print(f"🔍 Executing Web Query: {q}")
        raw_results.extend(_tavily_search(q, max_results=4))

    if not raw_results:
        print("⚠️ Web Search returned zero hits.")
        return {"evidence": []}

    try:
        extractor = llm.with_structured_output(EvidencePack)
        pack = extractor.invoke([
            SystemMessage(content=RESEARCH_SYSTEM),
            HumanMessage(content=f"Raw Search Results Payload:\n{raw_results}"),
        ])
        evidence_items = pack.evidence
    except Exception as e:
        print(f"⚠️ Research extraction mapping failed. Using parsing fallback. Error: {e}")
        evidence_items = [EvidenceItem(title=r["title"], URL=r["url"], snippet=r["snippet"]) for r in raw_results if
                          r.get("url")]

    dedup = {}
    for e in evidence_items:
        if e.URL:
            dedup[e.URL] = e

    print(f"💾 Structured Evidence Cache Populated: {len(dedup)} unique authority resources verified.")
    return {"evidence": list(dedup.values())}


# ----------------- PRODUCTION ORCHESTRATOR -----------------

ORCHESTRATOR_SYSTEM = """You are a Principal Developer Advocate and Systems Architect. Your job is to construct a rigorous, production-grade structural plan for a technical engineering blog post. 

You must strictly output a Plan object mapping perfectly to the requested schema guidelines.

CRITICAL STRUCTURAL CORE CONSTRAINTS:
1. Section Count: Generate exactly 5 to 7 logical sections (mapped to the Tasks array).
2. The 'common_mistakes' Safety Guard: You must assign `section_type="common_mistakes"` to EXACTLY ONE Task across the entire plan. No more, no less. Ensure its title focuses exclusively on anti-patterns and concrete failure modes.
3. TITLE HYGIENE BANS (ANTI-REPETITION CONSTRAINT):
   - ONLY the single task with `section_type="common_mistakes"` is permitted to have the phrase "Common Mistakes", "Errors", or "Pitfalls" in its title field.
   - For all other sections ("Intro", "core", "examples", "checklist", "conclusion"), it is STRICTLY FORBIDDEN to use the words "Mistakes", "Errors", "Pitfalls", "Flaws", or "Common". Give them constructive, execution-focused technical titles (e.g., "Designing Real-Time Monitoring Dashboards" instead of "Common Mistakes in Dashboards").
4. Architecture Progression: Organize the sections to respect an engineering journey: Problem/Context -> Mental Model/Intuition -> Technical Implementation -> Trade-off Matrix/Observability -> Conclusion/Next Steps.
5. Eliminate Vague Content: Every single item in the `bullets` array must contain an action verb dictating what to build, test, display, or benchmark. 
   - BANNED: "Discuss how X works", "Explain the concept of Y", "Look at Z".
   - REQUIRED: "Write a complete code block demonstrating atomic primitive locking", "Benchmark latency disparities between payload types A and B using a structured table", "Expose a Prometheus metric registration template for tracking system throughput".

TECHNICAL QUALITY REQUIREMENTS:
- Target an audience of battle-tested senior engineers. Avoid introductory metaphors.
- Incorporate tactical subpoints within your tasks covering: code fragments, explicit edge cases, underlying protocols, scaling/cost complexities, and telemetry requirements (logs, metrics, spans).
"""


def orchestrator(state: State) -> dict:
    mode = state.get("mode", "closed_book")
    evidence = state.get("evidence", []) or []

    # Send a minimal metadata map to the orchestrator to prevent context overloading
    serialized_meta = [{"title": e.title, "url": e.URL} for e in evidence][:10]

    plan = llm.with_structured_output(Plan).invoke([
        SystemMessage(content=ORCHESTRATOR_SYSTEM),
        HumanMessage(
            content=f"Topic: {state['topic']}\nExecution Mode: {mode}\nAvailable Structural Knowledge Context Indices:\n{serialized_meta}")
    ])
    return {"plan": plan}


# ----------------- PRODUCTION WORKER & FANOUT -----------------

def fanout(state: State):
    """
    PRODUCTION TASK-EVIDENCE ROUTER MATRIX
    Filters the global evidence pool programmatically. Each individual worker receives
    ONLY evidence objects matching tokens in their section title or goal statement.
    """
    global_evidence = state.get("evidence", []) or []
    actions = []

    for task in state["plan"].tasks:
        search_tokens = set(re.findall(r'\w+', (task.title + " " + task.goal).lower()))
        matched_evidence = []

        for item in global_evidence:
            item_text = ((item.title or "") + " " + (item.snippet or "")).lower()
            if any(token in item_text for token in search_tokens if len(token) > 3):
                matched_evidence.append(item.model_dump())

        if not matched_evidence and global_evidence:
            matched_evidence = [e.model_dump() for e in global_evidence[:3]]

        actions.append(
            Send("worker", {
                "task_id": task.id,
                "task_title": task.title,
                "task_goal": task.goal,
                "task_type": task.section_type,
                "task_bullets": task.bullets,
                "target_words": task.target_words,
                "requires_research": task.requires_research,
                "requires_citations": task.requires_citations,
                "requires_code": task.requires_code,
                "blog_title": state["plan"].blog_title,
                "audience": state["plan"].audience,
                "tone": state["plan"].tone,
                "isolated_evidence": matched_evidence
            })
        )
    return actions


WORKER_SYSTEM = """You are an expert Senior Technical Content Engineer and Core Systems Contributor. Your task is to write a single, isolated chapter of an engineering blog post based strictly on the isolated schema inputs provided.

PRIME PRODUCTION-GRADE CONTENT RULES:
1. Pure Title Hygiene: Open your output using exactly `## ` followed by the provided Cleaned Target Title. Do NOT modify it, do NOT append metadata suffix arrays, and do NOT inject words like "Common Mistakes" unless it is the dedicated mistakes node.
2. Context Manager Enforcement: Lock primitives must use native context handlers or explicit release guarantees.
   - CORRECT: `with self._lock:` or `self._lock.acquire()` followed by an explicit `try...finally: self._lock.release()` block.
   - BANNED: `with self._lock.acquire():` (this is a catastrophic syntax error that breaks multi-threading processing loops).
3. Code Completion & Execution Integrity: Avoid using ellipses (`...`) or blank assignments inside implementation paths. Replace dataset assignments or data loaders with small inline mock arrays or mock objects so the block is fully self-contained and runnable.
4. Hard Structural Type Adherence:
   - If your assigned task_type is 'common_mistakes', focus entirely on anti-patterns, code failure points, unhandled errors, or misconfigurations.
   - If your assigned task_type is NOT 'common_mistakes', you are FORBIDDEN from structuring this section around common mistakes. Focus strictly on your assigned constructive design domain.
5. Zero AI Fluff or Meta-Commentary: Do NOT summarize what your text tables show. 
   - BANNED PHRASES: "As shown in the table above...", "This table highlights...", "Now let us dive deep into...". 
   - Write cleanly and without conversational introductory filler. Begin delivering technical value from the first sentence.
"""


def worker(payload: dict) -> dict:
    bullets_text = "\n- " + "\n- ".join(payload["task_bullets"])

    # --- PRODUCTION TITLE SANITIZATION GUARD ---
    clean_title = payload["task_title"]
    if payload["task_type"] != "common_mistakes":
        clean_title = re.sub(r"(?i)\b(common\s+)?mistakes(\s+to\s+avoid|\s+in)?\s*(:\s*)?", "", clean_title)
        clean_title = re.sub(r"(?i)\b(pitfalls|errors|flaws)(\s+in)?\s*(:\s*)?", "", clean_title)
        clean_title = clean_title.strip("-: ").capitalize()
    # --------------------------------------------

    evidence_items = [EvidenceItem(**e) for e in payload.get("isolated_evidence", [])]
    evidence_text = ""
    if evidence_items and payload["requires_research"]:
        evidence_text = "\n".join(
            f"--- SOURCE ID: {idx} ---\nSource Title: {e.title}\nSource Reference Link: {e.URL}\nVerified Fact Payload: {e.snippet}\n"
            for idx, e in enumerate(evidence_items) if e.snippet
        )

    section_msg = llm.invoke([
        SystemMessage(content=WORKER_SYSTEM),
        HumanMessage(content=(
            f"Overall Blog Specifications:\n"
            f"- Targeted Audience Persona: {payload['audience']}\n"
            f"- Writing Style Constraint: {payload['tone']}\n\n"
            f"Your Isolated Chapter Instructions:\n"
            f"- Cleaned Target Title: {clean_title}\n"
            f"- Structural Section Type: {payload['task_type']}\n"
            f"- Core Goal Statement: {payload['task_goal']}\n"
            f"- Target Word Count Boundary: {payload['target_words']}\n"
            f"- Code Generation Requested: {payload['requires_code']}\n"
            f"- Exact Sub-Bullets to Fulfill:\n{bullets_text}\n\n"
            f"Verified External Technical Evidence Records (USE THIS CONTEXT TO ENFORCE TRUTH):\n"
            f"{evidence_text or 'No localized external evidence links provided.'}\n\n"
            f"Generate your isolated section text below following markdown parameters:"
        ))
    ])

    return {"sections": [section_msg.content.strip()]}


# ----------------- REDUCER -----------------

def reducer(state: State) -> dict:
    title = state["plan"].blog_title

    # Flatten collected markdown strings cleanly
    body = "\n\n".join(state["sections"]).strip()
    final_md = f"# {title}\n\n{body}\n"

    # Production-ready safe file sanitization
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower()
    slug = slug[:80]

    path = Path(f"{slug}.md")
    path.write_text(final_md, encoding="utf-8")

    print(f"🏁 System run successful. Output written cleanly to: {path.resolve()}")
    return {"final": final_md}


# ----------------- GRAPH COMPLIANCE MATRIX -----------------

g = StateGraph(State)
g.add_node("router", router_node)
g.add_node("research", research_node)
g.add_node("orchestrator", orchestrator)
g.add_node("worker", worker)
g.add_node("reducer", reducer)

g.add_edge(START, "router")
g.add_conditional_edges(
    "router",
    route_next,
    {"research": "research", "orchestrator": "orchestrator"}
)
g.add_edge("research", "orchestrator")

g.add_conditional_edges("orchestrator", fanout, ["worker"])
g.add_edge("worker", "reducer")
g.add_edge("reducer", END)

app = g.compile()