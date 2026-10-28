"""
Streamlit Web Application for Experiment 10: Task Automation Agent — Research Brief Generator.
Provides an interactive web interface for topic-based research briefs powered by DuckDuckGo and Groq.
"""

import streamlit as st
import time
from config import (
    get_system_status,
    get_model,
    is_api_key_configured,
    mask_api_key,
    MAX_TOPIC_LENGTH,
)
from agent import run_research_agent, metrics

# Page configuration
st.set_page_config(
    page_title="Task Automation Agent — Research Brief Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state variables
if "history" not in st.session_state:
    st.session_state.history = []

if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

# Custom styling for academic presentation
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .brief-card {
        background-color: #F8FAFC;
        border-left: 5px solid #2563EB;
        padding: 1.2rem;
        border-radius: 8px;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .metric-badge {
        display: inline-block;
        background-color: #EEF2FF;
        color: #3730A3;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .source-item {
        margin-bottom: 0.4rem;
        font-size: 0.92rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- SIDEBAR: Configuration & Monitoring ---
with st.sidebar:
    st.header("⚙️ Configuration & Status")
    
    # API Key Input (Allows runtime entry if .env is omitted)
    user_api_key = st.text_input(
        "Groq API Key (Optional Override):",
        type="password",
        placeholder="gsk_...",
        help="Enter your Groq key here or configure GROQ_API_KEY in your local .env file.",
    )
    
    # Model Selection / Override
    configured_model = get_model()
    model_choice = st.text_input(
        "Groq Model:",
        value=configured_model,
        help="Specify the target Groq LLM model ID (e.g. llama-3.3-70b-versatile, llama-3.1-8b-instant).",
    )
    
    st.divider()
    
    # System Status Panel (Credentials never leaked)
    st.subheader("📡 Service Status")
    status = get_system_status(user_api_key)
    
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Search Engine")
        st.write(f"🟢 **DuckDuckGo**")
    with col2:
        st.caption("LLM Provider")
        st.write(f"⚡ **Groq Cloud**")
        
    st.caption("API Key Configuration")
    if is_api_key_configured(user_api_key):
        st.success(f"Configured ({status['api_key_masked']})")
    else:
        st.error("Missing API Key")
        
    st.caption("Active Model")
    st.code(model_choice, language="text")

    st.divider()

    # In-memory Monitoring Metrics
    st.subheader("📊 Session Telemetry")
    stats = metrics.get_stats()
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("Total Requests", stats["total_requests"])
    m_col2.metric("Successful", stats["successful_requests"])
    
    if stats["failed_requests"] > 0:
        st.metric("Failed Requests", stats["failed_requests"])
    
    if stats["successful_requests"] > 0:
        st.caption(f"Avg Search Latency: **{stats['avg_search_seconds']}s**")
        st.caption(f"Avg LLM Latency: **{stats['avg_llm_seconds']}s**")

    st.info("ℹ️ Telemetry metrics are tracked in-process and reset when the server restarts.")


# --- MAIN INTERFACE ---
st.markdown('<div class="main-title">Task Automation Agent — Research Brief Generator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">'
    'Autonomous research pipeline: Live Web Search (DuckDuckGo) &rarr; Deduplication &rarr; Groq LLM Summarization &rarr; 3-Point Evidence-Based Brief.'
    '</div>',
    unsafe_allow_html=True,
)

# Topic Input Section
with st.container():
    topic_input = st.text_input(
        "Enter a research topic:",
        placeholder="e.g., Quantum Computing breakthroughs 2026, or MLOps best practices for LLMs",
        max_chars=MAX_TOPIC_LENGTH,
        help=f"Enter a concise technical topic. Maximum {MAX_TOPIC_LENGTH} characters.",
    )
    
    chars_left = MAX_TOPIC_LENGTH - len(topic_input)
    st.caption(f"Characters remaining: {chars_left}/{MAX_TOPIC_LENGTH}")

    generate_clicked = st.button("🚀 Generate Research Brief", type="primary", use_container_width=True)

# Agent Execution Flow
if generate_clicked:
    if not topic_input.strip():
        st.warning("⚠️ Please enter a research topic before clicking Generate.")
    elif not is_api_key_configured(user_api_key):
        st.error(
            "🔑 Groq API Key is not configured! Please provide your key in the sidebar or "
            "set `GROQ_API_KEY` in your `.env` file."
        )
    else:
        with st.spinner("🔍 Agent running: Fetching real-time web results and generating 3-point brief via Groq..."):
            result = run_research_agent(
                topic=topic_input,
                api_key=user_api_key if user_api_key.strip() else None,
                model=model_choice if model_choice.strip() else None,
            )
            st.session_state.latest_result = result
            if result["success"]:
                st.session_state.history.append({
                    "topic": result["topic"],
                    "bullets": result["bullet_points"],
                    "time": result["timings"]["total_seconds"],
                    "timestamp": time.strftime("%H:%M:%S"),
                })

# Render Latest Results
if st.session_state.latest_result:
    res = st.session_state.latest_result
    
    if res["success"]:
        st.success(f"✅ Research Brief generated successfully for: **{res['topic']}**")
        
        # Latency / Timing Metrics
        timings = res["timings"]
        st.markdown(
            f'<div style="margin-bottom: 0.8rem;">'
            f'<span class="metric-badge">⚡ Total: {timings["total_seconds"]}s</span>'
            f'<span class="metric-badge">🌐 Search: {timings["search_seconds"]}s</span>'
            f'<span class="metric-badge">🤖 LLM: {timings["llm_seconds"]}s</span>'
            f'<span class="metric-badge">📄 Sources: {res["raw_results_count"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # The 3-Bullet Research Brief
        st.subheader("📋 3-Point Research Brief")
        st.markdown('<div class="brief-card">', unsafe_allow_html=True)
        for idx, bullet in enumerate(res["bullet_points"], 1):
            st.markdown(f"**{idx}.** {bullet}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Sources Section (Separate from the 3 bullets as required)
        st.subheader("🔗 Cited Web Sources")
        if res["sources"]:
            for src in res["sources"]:
                st.markdown(
                    f'<div class="source-item">• <a href="{src["url"]}" target="_blank">{src["title"]}</a></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.write("No source links available.")
            
    else:
        st.error(f"❌ Failed to generate brief: {res.get('error', 'Unknown agent error occurred.')}")
        st.info("💡 Tip: Verify your network connection, your topic phrasing, or check that your Groq API key is active.")

# Current Session Query History
if st.session_state.history:
    with st.expander(f"📜 Session Search History ({len(st.session_state.history)} searches)", expanded=False):
        for idx, item in enumerate(reversed(st.session_state.history), 1):
            st.markdown(f"**{item['timestamp']}** — *{item['topic']}* (Latency: {item['time']}s)")
            for b in item["bullets"]:
                st.caption(f"• {b}")
            st.divider()
