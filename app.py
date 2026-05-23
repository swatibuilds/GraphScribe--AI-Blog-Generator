import streamlit as st
from pathlib import Path
import re
import json

# Import your LangGraph app
from research_blog_writer import app


# =====================================================
# Page configuration
# =====================================================
st.set_page_config(
    page_title="GraphScribe — AI Blog Engine",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================
# Global CSS — Dark editorial, cinematic, premium SaaS
# =====================================================
st.markdown(
    """
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap');

    /* ── Root tokens ── */
    :root {
        --bg:          #0a0a0f;
        --bg-1:        #0f0f18;
        --bg-2:        #13131e;
        --bg-glass:    rgba(255,255,255,0.035);
        --border:      rgba(255,255,255,0.07);
        --border-hi:   rgba(255,255,255,0.14);
        --accent:      #c8f04a;
        --accent-dim:  rgba(200,240,74,0.12);
        --accent-glow: rgba(200,240,74,0.25);
        --text:        #e8e8f0;
        --muted:       #6b6b80;
        --muted-2:     #4a4a5a;
        --danger:      #ff5a5a;
        --info:        #60a5fa;
        --font-head:   'Syne', sans-serif;
        --font-serif:  'Instrument Serif', serif;
        --font-mono:   'DM Mono', monospace;
    }

    /* ── Base resets ── */
    html, body, [data-testid="stApp"] {
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: var(--font-head);
    }

    /* Animated mesh background */
    [data-testid="stApp"]::before {
        content: '';
        position: fixed;
        inset: 0;
        z-index: 0;
        background:
            radial-gradient(ellipse 80% 50% at 20% -10%, rgba(200,240,74,0.06) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 90% 110%, rgba(96,165,250,0.05) 0%, transparent 60%),
            radial-gradient(ellipse 100% 80% at 50% 50%, rgba(255,255,255,0.01) 0%, transparent 100%);
        pointer-events: none;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--muted-2); border-radius: 99px; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--bg-1) !important;
        border-right: 1px solid var(--border) !important;
        padding-top: 0 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    /* Sidebar header brand block */
    .gs-brand {
        padding: 0 0 1.4rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.4rem;
    }
    .gs-brand-logo {
        font-family: var(--font-head);
        font-weight: 800;
        font-size: 1.55rem;
        letter-spacing: -0.03em;
        color: var(--text);
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }
    .gs-brand-logo span.accent { color: var(--accent); }
    .gs-brand-tagline {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--muted);
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 0.25rem;
    }

    /* ── Sidebar input labels ── */
    [data-testid="stSidebar"] label {
        font-family: var(--font-mono) !important;
        font-size: 0.72rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        color: var(--muted) !important;
    }

    /* ── Text input ── */
    [data-testid="stTextInput"] input {
        background: var(--bg-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
        font-family: var(--font-head) !important;
        font-size: 0.9rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
        padding: 0.65rem 0.85rem !important;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-dim) !important;
        outline: none !important;
    }
    [data-testid="stTextInput"] input::placeholder { color: var(--muted-2) !important; }

    /* ── Primary button ── */
    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        color: #0a0a0f !important;
        font-family: var(--font-head) !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        letter-spacing: 0.04em !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.65rem 1.4rem !important;
        cursor: pointer !important;
        transition: transform 0.15s, box-shadow 0.2s !important;
        box-shadow: 0 0 0 0 var(--accent-glow) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 24px var(--accent-glow) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:active {
        transform: translateY(0) !important;
    }

    /* ── Secondary / download button ── */
    .stDownloadButton > button {
        background: transparent !important;
        border: 1px solid var(--border-hi) !important;
        color: var(--text) !important;
        font-family: var(--font-mono) !important;
        font-size: 0.78rem !important;
        border-radius: 8px !important;
        transition: border-color 0.2s, background 0.2s !important;
    }
    .stDownloadButton > button:hover {
        border-color: var(--accent) !important;
        background: var(--accent-dim) !important;
        color: var(--accent) !important;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] [role="tablist"] {
        border-bottom: 1px solid var(--border) !important;
        gap: 0 !important;
    }
    [data-testid="stTabs"] button[role="tab"] {
        font-family: var(--font-mono) !important;
        font-size: 0.74rem !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: var(--muted) !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 0.6rem 1.1rem !important;
        transition: color 0.2s !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom-color: var(--accent) !important;
    }
    [data-testid="stTabs"] button[role="tab"]:hover {
        color: var(--text) !important;
    }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 1rem 1.2rem !important;
        backdrop-filter: blur(12px) !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--font-mono) !important;
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        color: var(--muted) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: var(--font-head) !important;
        font-weight: 700 !important;
        color: var(--text) !important;
        font-size: 1.25rem !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        margin-bottom: 0.6rem !important;
        backdrop-filter: blur(8px) !important;
        overflow: hidden !important;
    }
    [data-testid="stExpander"] summary {
        font-family: var(--font-head) !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: var(--text) !important;
        padding: 0.85rem 1.1rem !important;
    }
    [data-testid="stExpander"] summary:hover { color: var(--accent) !important; }
    [data-testid="stExpander"] > div > div {
        padding: 0 1.1rem 1rem 1.1rem !important;
    }

    /* ── Code blocks ── */
    code, .stCode {
        background: var(--bg-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        font-family: var(--font-mono) !important;
        font-size: 0.82rem !important;
        color: var(--accent) !important;
    }

    /* ── Info / warning / spinner ── */
    [data-testid="stAlert"] {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-hi) !important;
        border-radius: 10px !important;
        font-family: var(--font-head) !important;
        color: var(--text) !important;
    }
    .stSpinner > div {
        border-top-color: var(--accent) !important;
    }

    /* ── JSON viewer ── */
    [data-testid="stJson"] {
        background: var(--bg-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        font-family: var(--font-mono) !important;
        font-size: 0.78rem !important;
    }

    /* ── Markdown body (blog content) ── */
    .blog-render h1, .blog-render h2, .blog-render h3 {
        font-family: var(--font-serif) !important;
        color: var(--text) !important;
    }
    .blog-render h1 { font-size: 2.2rem; line-height: 1.2; margin-bottom: 0.5rem; }
    .blog-render h2 { font-size: 1.55rem; margin-top: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }
    .blog-render h3 { font-size: 1.15rem; color: var(--accent) !important; }
    .blog-render p  { font-family: var(--font-head); font-size: 0.97rem; line-height: 1.8; color: var(--text); }
    .blog-render a  { color: var(--accent); text-decoration: underline dotted; }
    .blog-render blockquote {
        border-left: 3px solid var(--accent);
        padding-left: 1rem;
        color: var(--muted);
        font-style: italic;
        font-family: var(--font-serif);
        font-size: 1.05rem;
    }
    .blog-render code { background: var(--bg-2); padding: 0.15em 0.4em; border-radius: 4px; font-family: var(--font-mono); font-size: 0.82em; color: var(--accent); }
    .blog-render pre  { background: var(--bg-2); border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; overflow-x: auto; }

    /* Dividers */
    hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.6rem 0 !important; }

    /* Sidebar caption */
    [data-testid="stSidebar"] .stCaption {
        font-family: var(--font-mono) !important;
        font-size: 0.72rem !important;
        color: var(--muted) !important;
        line-height: 1.7 !important;
    }

    /* Subheader override */
    h2, h3 { font-family: var(--font-head) !important; font-weight: 700 !important; }

    /* ── Page hero ── */
    .gs-hero {
        padding: 2.2rem 0 1.6rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
        animation: fadeSlideDown 0.55s ease both;
    }
    .gs-hero-eyebrow {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 0.6rem;
    }
    .gs-hero-title {
        font-family: var(--font-serif);
        font-size: 2.6rem;
        font-weight: 400;
        line-height: 1.15;
        color: var(--text);
        margin: 0 0 0.5rem 0;
    }
    .gs-hero-title em { font-style: italic; color: var(--accent); }
    .gs-hero-sub {
        font-family: var(--font-mono);
        font-size: 0.78rem;
        color: var(--muted);
        letter-spacing: 0.04em;
    }

    /* ── Status pill ── */
    .gs-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.75rem;
        border-radius: 99px;
        font-family: var(--font-mono);
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .gs-pill-green { background: rgba(200,240,74,0.1); color: var(--accent); border: 1px solid rgba(200,240,74,0.25); }
    .gs-pill-blue  { background: rgba(96,165,250,0.1); color: var(--info);   border: 1px solid rgba(96,165,250,0.25); }
    .gs-pill-red   { background: rgba(255,90,90,0.1);  color: var(--danger); border: 1px solid rgba(255,90,90,0.25); }
    .gs-pill::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

    /* ── Evidence card ── */
    .gs-evidence-card {
        background: var(--bg-glass);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        backdrop-filter: blur(8px);
        transition: border-color 0.2s, transform 0.2s;
        animation: fadeSlideUp 0.4s ease both;
    }
    .gs-evidence-card:hover {
        border-color: var(--border-hi);
        transform: translateY(-2px);
    }
    .gs-evidence-title {
        font-family: var(--font-head);
        font-weight: 600;
        font-size: 0.92rem;
        color: var(--text);
        text-decoration: none;
    }
    .gs-evidence-title:hover { color: var(--accent); }
    .gs-evidence-meta {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--muted);
        margin-top: 0.35rem;
        letter-spacing: 0.04em;
    }

    /* ── Sidebar feature list ── */
    .gs-feature {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        margin-bottom: 0.7rem;
    }
    .gs-feature-icon {
        color: var(--accent);
        font-size: 0.8rem;
        margin-top: 0.12rem;
        flex-shrink: 0;
    }
    .gs-feature-text {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--muted);
        line-height: 1.5;
    }

    /* ── Log card ── */
    .gs-log-row {
        display: flex;
        align-items: center;
        gap: 0.9rem;
        padding: 0.7rem 1rem;
        border-bottom: 1px solid var(--border);
        font-family: var(--font-mono);
        font-size: 0.78rem;
        animation: fadeSlideUp 0.35s ease both;
    }
    .gs-log-row:last-child { border-bottom: none; }
    .gs-log-key { color: var(--muted); width: 160px; flex-shrink: 0; }
    .gs-log-val { color: var(--text); }

    /* ── Animations ── */
    @keyframes fadeSlideDown {
        from { opacity: 0; transform: translateY(-16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 0 0 var(--accent-glow); }
        50%       { box-shadow: 0 0 0 8px transparent; }
    }

    /* spinner text override */
    [data-testid="stSpinner"] p {
        font-family: var(--font-mono) !important;
        font-size: 0.78rem !important;
        color: var(--muted) !important;
        letter-spacing: 0.06em !important;
    }

    /* Stagger animation on plan expanders */
    [data-testid="stExpander"]:nth-child(1) { animation-delay: 0.05s; }
    [data-testid="stExpander"]:nth-child(2) { animation-delay: 0.10s; }
    [data-testid="stExpander"]:nth-child(3) { animation-delay: 0.15s; }
    [data-testid="stExpander"]:nth-child(4) { animation-delay: 0.20s; }
    [data-testid="stExpander"]:nth-child(5) { animation-delay: 0.25s; }
    [data-testid="stExpander"] { animation: fadeSlideUp 0.45s ease both; }

    /* ── Main content area padding ── */
    .block-container {
        padding-top: 0 !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 1280px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# Sidebar — Branding + Input
# =====================================================
with st.sidebar:
    st.markdown(
        """
        <div class="gs-brand">
            <div class="gs-brand-logo">✦ Graph<span class="accent">Scribe</span></div>
            <div class="gs-brand-tagline">AI-Powered Blog Engine</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    topic = st.text_input(
        "Blog topic",
        placeholder="e.g. State of multimodal LLMs in 2026",
        label_visibility="visible",
    )

    generate_btn = st.button(
        "✦  Generate Blog",
        type="primary",
        use_container_width=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        """
        <div style="margin-bottom:0.5rem; font-family:var(--font-mono); font-size:0.7rem; letter-spacing:0.1em; text-transform:uppercase; color:var(--muted);">
            How it works
        </div>
        <div class="gs-feature">
            <div class="gs-feature-icon">◈</div>
            <div class="gs-feature-text">Plans a structured technical blog with audience & tone</div>
        </div>
        <div class="gs-feature">
            <div class="gs-feature-icon">◈</div>
            <div class="gs-feature-text">Performs live research when context is needed</div>
        </div>
        <div class="gs-feature">
            <div class="gs-feature-icon">◈</div>
            <div class="gs-feature-text">Writes each section via specialized LangGraph agents</div>
        </div>
        <div class="gs-feature">
            <div class="gs-feature-icon">◈</div>
            <div class="gs-feature-text">Outputs clean, publish-ready Markdown</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================
# Session state
# =====================================================
if "result" not in st.session_state:
    st.session_state.result = None


# =====================================================
# Run graph
# =====================================================
if generate_btn:
    if not topic.strip():
        st.sidebar.warning("Please enter a blog topic first.")
    else:
        with st.spinner("GraphScribe is researching and writing your blog…"):
            result = app.invoke({"topic": topic})
            st.session_state.result = result


# =====================================================
# Page Hero
# =====================================================
st.markdown(
    """
    <div class="gs-hero">
        <div class="gs-hero-eyebrow">✦ GraphScribe — Research-Aware Pipeline</div>
        <h1 class="gs-hero-title">Generated <em>Technical Blog</em></h1>
        <div class="gs-hero-sub">Auto-generated using a multi-agent LangGraph pipeline with live research</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# Empty state
# =====================================================
if st.session_state.result is None:
    st.markdown(
        """
        <div style="
            background: var(--bg-glass);
            border: 1px dashed var(--border-hi);
            border-radius: 14px;
            padding: 3.5rem 2rem;
            text-align: center;
            margin-top: 1rem;
            backdrop-filter: blur(8px);
        ">
            <div style="font-size: 2.4rem; margin-bottom: 0.8rem;">✦</div>
            <div style="font-family: var(--font-head); font-size: 1.2rem; font-weight: 600; color: var(--text); margin-bottom: 0.5rem;">
                Ready to write
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--muted); max-width: 340px; margin: 0 auto; line-height: 1.7;">
                Enter a blog topic in the sidebar and click <strong style="color:var(--accent)">Generate Blog</strong> to start the pipeline.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


result = st.session_state.result
plan = result["plan"]
final_md = result["final"]


# =====================================================
# Tabs
# =====================================================
tab_blog, tab_plan, tab_research, tab_logs = st.tabs(
    ["📝  Blog", "🧠  Plan", "🔍  Research", "📜  Logs"]
)


# =====================================================
# Blog tab
# =====================================================
with tab_blog:
    # Blog meta bar
    needs_research = result.get("needs_research", False)
    mode = result.get("mode", "unknown")

    pill_class = "gs-pill-green" if needs_research else "gs-pill-blue"
    pill_label = "Research-Backed" if needs_research else "Knowledge-Based"
    mode_pill_class = "gs-pill-blue"

    st.markdown(
        f"""
        <div style="display:flex; gap:0.6rem; align-items:center; margin-bottom:1.6rem; flex-wrap:wrap;">
            <span class="gs-pill {pill_class}">{pill_label}</span>
            <span class="gs-pill {mode_pill_class}">{mode}</span>
            <span class="gs-pill gs-pill-green">{len(plan.tasks)} sections</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Blog content in styled container
    st.markdown(
        f'<div class="blog-render">{__import__("mistune").html(final_md)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", plan.blog_title).strip("_").lower()[:80]
    col_dl, col_space = st.columns([1, 4])
    with col_dl:
        st.download_button(
            label="⬇  Download Markdown",
            data=final_md,
            file_name=f"{slug}.md",
            mime="text/markdown",
        )


# =====================================================
# Plan tab
# =====================================================
with tab_plan:
    st.markdown(
        f"""
        <div style="margin-bottom:1.4rem;">
            <div style="font-family:var(--font-serif); font-size:1.7rem; color:var(--text); margin-bottom:0.3rem;">
                {plan.blog_title}
            </div>
            <div style="font-family:var(--font-mono); font-size:0.72rem; color:var(--muted); letter-spacing:0.06em;">
                {len(plan.tasks)} sections planned
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Audience", plan.audience)
    col2.metric("Tone", plan.tone)
    col3.metric("Sections", len(plan.tasks))

    st.markdown("<hr>", unsafe_allow_html=True)

    for idx, task in enumerate(plan.tasks, start=1):
        with st.expander(f"Section {idx} — {task.title}", expanded=False):
            st.markdown(
                f"""
                <div style="font-family:var(--font-mono); font-size:0.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.6rem;">
                    {task.section_type} · {task.target_words} words
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f"**Goal** — {task.goal}")

            st.markdown(
                "<div style='margin-top:0.8rem; font-family:var(--font-mono); font-size:0.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.4rem;'>Coverage</div>",
                unsafe_allow_html=True,
            )
            for bullet in task.bullets:
                st.markdown(
                    f"<div style='display:flex; gap:0.5rem; margin-bottom:0.3rem; font-size:0.88rem;'><span style='color:var(--accent);'>◈</span><span>{bullet}</span></div>",
                    unsafe_allow_html=True,
                )


# =====================================================
# Research tab
# =====================================================
with tab_research:
    needs = result.get("needs_research", False)
    mode_val = result.get("mode", "unknown")
    queries = result.get("queries", [])
    evidence = result.get("evidence", [])

    # Summary row
    st.markdown(
        f"""
        <div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:1.6rem;">
            <span class="gs-pill {'gs-pill-green' if needs else 'gs-pill-blue'}">
                {'Research active' if needs else 'No research needed'}
            </span>
            <span class="gs-pill gs-pill-blue">mode: {mode_val}</span>
            <span class="gs-pill gs-pill-blue">{len(queries)} queries</span>
            <span class="gs-pill gs-pill-blue">{len(evidence)} sources</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Queries
    st.markdown(
        "<div style='font-family:var(--font-mono); font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:var(--muted); margin-bottom:0.75rem;'>Generated Queries</div>",
        unsafe_allow_html=True,
    )
    if queries:
        for q in queries:
            st.code(q, language="text")
    else:
        st.markdown(
            "<div style='font-family:var(--font-mono); font-size:0.78rem; color:var(--muted-2);'>No queries generated — topic was handled from parametric knowledge.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # Evidence
    st.markdown(
        "<div style='font-family:var(--font-mono); font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:var(--muted); margin-bottom:0.75rem;'>Evidence Used</div>",
        unsafe_allow_html=True,
    )
    if evidence:
        for e in evidence:
            source_label = e.source or "unknown"
            date_label = e.published_at or "unknown"
            st.markdown(
                f"""
                <div class="gs-evidence-card">
                    <a href="{e.URL}" target="_blank" class="gs-evidence-title">{e.title}</a>
                    <div class="gs-evidence-meta">
                        <span style="color:var(--accent);">◈</span> {source_label}
                        &nbsp;·&nbsp; {date_label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='font-family:var(--font-mono); font-size:0.78rem; color:var(--muted-2);'>No external sources were used.</div>",
            unsafe_allow_html=True,
        )


# =====================================================
# Logs tab
# =====================================================
with tab_logs:
    st.markdown(
        "<div style='font-family:var(--font-mono); font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:var(--muted); margin-bottom:1rem;'>Pipeline Execution Trace</div>",
        unsafe_allow_html=True,
    )

    log_data = {
        "mode": result.get("mode"),
        "needs_research": result.get("needs_research"),
        "queries": result.get("queries"),
        "sections_generated": len(result.get("sections", [])),
    }

    # Stylised table view
    st.markdown(
        """
        <div style="background:var(--bg-glass); border:1px solid var(--border); border-radius:10px; overflow:hidden; margin-bottom:1.2rem;">
        """,
        unsafe_allow_html=True,
    )
    for k, v in log_data.items():
        v_display = str(v) if not isinstance(v, list) else f"[{len(v)} items]"
        st.markdown(
            f"""
            <div class="gs-log-row">
                <div class="gs-log-key">{k}</div>
                <div class="gs-log-val">{v_display}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Raw JSON underneath
    with st.expander("Raw JSON output", expanded=False):
        st.json(log_data)