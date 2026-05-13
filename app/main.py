"""
Streamlit Chat UI for the Peakvisory AI Assistant.
Runs as: py -3.13 -m streamlit run app/main.py  (from project root)
"""
import os 
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.agent.finance_agent import finance_agent
from src.config import settings

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Peakvisory Assistant",
    page_icon="assets/favicon.png" if os.path.exists("assets/favicon.png") else "💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide the Streamlit header bar */
    header[data-testid="stHeader"] { display: none; }

    /* App background */
    .stApp { background-color: #0f1117; }

    /* Main chat area max-width */
    .block-container { max-width: 860px; padding-top: 2rem; }

    /* Welcome card */
    .welcome-card {
        text-align: center;
        padding: 3rem 2rem 1.5rem 2rem;
    }
    .welcome-icon {
        font-size: 3.5rem;
        margin-bottom: 0.5rem;
    }
    .welcome-title {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.4rem;
    }
    .welcome-sub {
        font-size: 1rem;
        color: #9ca3af;
        margin-bottom: 2rem;
    }

    /* Suggestion chips */
    div[data-testid="column"] .stButton > button {
        width: 100%;
        background: #1e2130;
        border: 1px solid #2d3148;
        border-radius: 12px;
        color: #d1d5db;
        font-size: 0.85rem;
        padding: 0.75rem 1rem;
        text-align: left;
        transition: all 0.2s ease;
        white-space: normal;
        height: auto;
        min-height: 60px;
    }
    div[data-testid="column"] .stButton > button:hover {
        background: #252840;
        border-color: #4f6ef7;
        color: #ffffff !important;
    }

    /* Chat messages — bright cream text for readability on dark bg */
    [data-testid="stChatMessage"] {
        background: transparent;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div {
        color: #f5f0e8 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #161922;
    }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "triggered_prompt" not in st.session_state:
    st.session_state.triggered_prompt = None


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Peakvisory AI")
    st.caption("Internal Knowledge Assistant")
    st.divider()
    if st.button("New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.triggered_prompt = None
        st.rerun()
    st.divider()
    st.caption(f"Model: `{settings.AGENT_MODEL}`")
    st.caption("Knowledge Base: Qdrant (Hybrid Search)")


# ── Welcome screen (shown only when no messages exist) ───────────────────────
SUGGESTED_PROMPTS = [
    "What are Peakvisory's pricing packages?",
    "What is the turnaround time for VAT returns?",
    "Who are the directors of Peakvisory?",
    "What accounting software does Peakvisory use?",
    "How does the onboarding process work?",
    "What is the Follow the Sun model?",
]

if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-icon">💼</div>
        <div class="welcome-title">Hi, I'm your Assistant</div>
        <div class="welcome-sub">Ask me anything about our services, pricing, onboarding, or company policies.</div>
    </div>
    """, unsafe_allow_html=True)

    # Suggestion chips — 2 rows of 3
    cols1 = st.columns(3)
    cols2 = st.columns(3)
    all_cols = cols1 + cols2
    for i, (col, prompt_text) in enumerate(zip(all_cols, SUGGESTED_PROMPTS)):
        with col:
            if st.button(prompt_text, key=f"suggestion_{i}"):
                st.session_state.triggered_prompt = prompt_text
                st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)


# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ── Response extractor ────────────────────────────────────────────────────────
def _extract_text(result) -> str:
    """Robustly extract clean plain text from any pydantic-ai AgentRunResult."""
    resp = getattr(result, "response", result)
    if hasattr(resp, "parts") and resp.parts:
        texts = [
            part.content.strip()
            for part in resp.parts
            if hasattr(part, "content") and isinstance(part.content, str) and part.content.strip()
        ]
        if texts:
            full_text = "\n\n".join(texts)
            # Check if it looks like a raw tool call or JSON (gibberish)
            if any(x in full_text for x in ["<function", "=search_kb", "{\"query\":"]) or full_text.strip().startswith("{"):
                return "I'm sorry, I had trouble processing that request. Please try rephrasing your question."
            return full_text
    if hasattr(resp, "text") and resp.text:
        return resp.text.strip()
    if isinstance(resp, str):
        if any(x in resp for x in ["<function", "=search_kb", "{\"query\":"]) or resp.strip().startswith("{"):
            return "I'm sorry, I had trouble processing that request. Please try rephrasing your question."
        return resp.strip()
    return str(resp)


# ── Input handler (typed or chip-triggered) ───────────────────────────────────
user_input = st.chat_input("Ask me anything about Peakvisory...")
active_prompt = user_input or st.session_state.triggered_prompt

if active_prompt:
    # Clear the chip trigger so it doesn't fire again
    st.session_state.triggered_prompt = None

    st.session_state.messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user"):
        st.markdown(active_prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                async def _run():
                    return await finance_agent.run(active_prompt)

                result = asyncio.run(_run())
                response = _extract_text(result)
            except Exception as exc:
                response = f"Something went wrong. Please try again. (Detail: {exc})"

        placeholder.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
