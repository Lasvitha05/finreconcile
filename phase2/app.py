import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinReconcile",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

    /* Global */
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* Hide default Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* App background */
    .stApp {
        background-color: #0f1117;
        color: #e2e8f0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b27;
        border-right: 1px solid #2d3748;
    }

    [data-testid="stSidebar"] .stTextArea textarea {
        background-color: #0f1117;
        color: #a0aec0;
        border: 1px solid #2d3748;
        border-radius: 6px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
    }

    [data-testid="stSidebar"] .stTextArea textarea:focus {
        border-color: #4fd1c5;
        box-shadow: 0 0 0 1px #4fd1c5;
    }

    /* Chat messages */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 0 1rem 120px 1rem;
    }

    .msg-user {
        background: #1e2a3a;
        border: 1px solid #2d3748;
        border-radius: 12px 12px 2px 12px;
        padding: 14px 18px;
        margin: 12px 0;
        margin-left: 15%;
        color: #e2e8f0;
        font-size: 14px;
        line-height: 1.6;
    }

    .msg-bot {
        background: #161b27;
        border: 1px solid #2d3748;
        border-left: 3px solid #4fd1c5;
        border-radius: 2px 12px 12px 12px;
        padding: 14px 18px;
        margin: 12px 0;
        margin-right: 8%;
        color: #e2e8f0;
        font-size: 14px;
        line-height: 1.6;
    }

    .msg-bot table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 13px;
    }

    .msg-bot th {
        background: #1e2a3a;
        color: #4fd1c5;
        padding: 8px 12px;
        text-align: left;
        font-weight: 600;
        border-bottom: 1px solid #2d3748;
    }

    .msg-bot td {
        padding: 8px 12px;
        border-bottom: 1px solid #1e2a3a;
        color: #cbd5e0;
    }

    .label-user {
        font-size: 11px;
        color: #718096;
        text-align: right;
        margin-bottom: 4px;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: 0.05em;
    }

    .label-bot {
        font-size: 11px;
        color: #4fd1c5;
        margin-bottom: 4px;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: 0.05em;
    }

    /* Header */
    .app-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        border-bottom: 1px solid #2d3748;
        margin-bottom: 1.5rem;
    }

    .app-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.6rem;
        font-weight: 600;
        color: #4fd1c5;
        letter-spacing: -0.02em;
    }

    .app-subtitle {
        font-size: 13px;
        color: #718096;
        margin-top: 4px;
    }

    /* Sidebar header */
    .sidebar-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        color: #4fd1c5;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 8px;
        margin-top: 16px;
    }

    /* Analyze button */
    .stButton > button {
        background: linear-gradient(135deg, #4fd1c5, #38b2ac);
        color: #0f1117;
        border: none;
        border-radius: 6px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.05em;
        padding: 10px 0;
        width: 100%;
        cursor: pointer;
        transition: opacity 0.2s;
    }

    .stButton > button:hover {
        opacity: 0.85;
        color: #0f1117;
    }

    /* Reset button */
    .reset-btn > button {
        background: transparent !important;
        color: #e53e3e !important;
        border: 1px solid #e53e3e !important;
        margin-top: 8px;
    }

    .reset-btn > button:hover {
        background: #e53e3e !important;
        color: white !important;
        opacity: 1 !important;
    }

    /* Welcome state */
    .welcome-box {
        text-align: center;
        padding: 4rem 2rem;
        color: #4a5568;
    }

    .welcome-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .welcome-text {
        font-size: 15px;
        line-height: 1.8;
        max-width: 420px;
        margin: 0 auto;
    }

    /* Chat input styling */
    .stChatInput {
        background: #161b27 !important;
    }

    [data-testid="stChatInput"] {
        background: #161b27;
        border-top: 1px solid #2d3748;
    }

    /* Status badges */
    .badge-ready {
        display: inline-block;
        background: #1a2e1a;
        color: #68d391;
        border: 1px solid #276749;
        border-radius: 4px;
        font-size: 11px;
        font-family: 'IBM Plex Mono', monospace;
        padding: 2px 8px;
        margin-top: 8px;
    }

    .badge-empty {
        display: inline-block;
        background: #2d2010;
        color: #f6ad55;
        border: 1px solid #744210;
        border-radius: 4px;
        font-size: 11px;
        font-family: 'IBM Plex Mono', monospace;
        padding: 2px 8px;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are FinReconcile, a senior financial reconciliation analyst with 15 years
of experience at Big 4 accounting firms.

FIRST ANALYSIS — when given two datasets:
1. Produce a full comparison table with every record side by side
2. Rank every mismatch by dollar impact — largest first
3. For each mismatch write: what the discrepancy is, the most likely cause
   (timing difference, manual entry error, payment method mismatch, system
   sync failure, partial payment, duplicate entry), and the exact action
   the finance team should take
4. End with a summary: total records, matched count, mismatch count, net
   dollar difference

FOLLOW-UP QUESTIONS — when the user asks for clarification:
- Always reference the specific invoice numbers and amounts from the data
- Give concrete, actionable answers — not generic explanations
- If asked to "explain better" or "go deeper", pick the single most
  important mismatch and walk through the full investigation steps a
  real accountant would take
- Never ask the user to re-paste data that's already in the conversation

TONE: Direct, precise, professional. You are talking to a CFO or Controller
who has no time for vague answers.
"""


# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "client" not in st.session_state:
    st.session_state.client = Anthropic()

if "data_submitted" not in st.session_state:
    st.session_state.data_submitted = False


# ── Helper: call Claude ────────────────────────────────────────────────────────
def call_claude(user_message: str) -> str:
    st.session_state.messages.append({
        "role": "user",
        "content": user_message
    })

    response = st.session_state.client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=st.session_state.messages
    )

    reply = response.content[0].text

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })

    return reply


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="app-title" style="font-size:1.2rem;">💰 FinReconcile</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle" style="font-size:11px; color:#718096;">AI Financial Reconciliation</div>', unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="sidebar-header">📋 Source A</div>', unsafe_allow_html=True)
    source_a_label = st.text_input("Label (e.g. Stripe, Bank Statement)", value="Stripe", key="label_a")
    source_a_data = st.text_area(
        "Paste data",
        height=160,
        placeholder="INV-001  $12,500  Acme Corp  Jan 5\nINV-002  $8,200   Beta LLC   Jan 8\n...",
        key="data_a"
    )

    st.markdown('<div class="sidebar-header">📋 Source B</div>', unsafe_allow_html=True)
    source_b_label = st.text_input("Label (e.g. QuickBooks, Ledger)", value="QuickBooks", key="label_b")
    source_b_data = st.text_area(
        "Paste data",
        height=160,
        placeholder="INV-001  $12,500  Acme Corp  Jan 5\nINV-002  $7,900   Beta LLC   Jan 9\n...",
        key="data_b"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Status badge
    if source_a_data.strip() and source_b_data.strip():
        st.markdown('<span class="badge-ready">✓ Both datasets ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-empty">⚠ Paste both datasets above</span>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    analyze_clicked = st.button("🔍 Analyze Mismatches", disabled=not (source_a_data.strip() and source_b_data.strip()))

    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    reset_clicked = st.button("↺ Reset Session")
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="font-size:11px; color:#4a5568; font-family: IBM Plex Mono, monospace;">Phase 2 — Streamlit UI<br>Model: claude-sonnet-4-6</div>', unsafe_allow_html=True)


# ── Handle reset ───────────────────────────────────────────────────────────────
if reset_clicked:
    st.session_state.messages = []
    st.session_state.data_submitted = False
    st.rerun()


# ── Main panel ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-title">FinReconcile</div>
    <div class="app-subtitle">Paste your financial data in the sidebar → get instant mismatch analysis</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Welcome state — no messages yet
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-box">
        <div class="welcome-icon">📊</div>
        <div class="welcome-text">
            Paste your two financial datasets in the sidebar and click
            <strong style="color:#4fd1c5;">Analyze Mismatches</strong> to begin.<br><br>
            Once analyzed, use the chat bar below to ask follow-up questions
            without re-pasting your data.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Render conversation history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="label-user">YOU</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="label-bot">FINRECONCILE</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msg-bot">{msg["content"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# ── Handle Analyze button ──────────────────────────────────────────────────────
if analyze_clicked:
    prompt = f"""Please reconcile the following two financial datasets:

**{source_a_label} Records:**
{source_a_data}

**{source_b_label} Records:**
{source_b_data}

Find all mismatches, rank them by dollar impact, explain each one, and tell me what to investigate."""

    with st.spinner("Analyzing mismatches..."):
        call_claude(prompt)
        st.session_state.data_submitted = True
    st.rerun()


# ── Follow-up chat input ───────────────────────────────────────────────────────
if st.session_state.data_submitted:
    followup = st.chat_input("Ask a follow-up question about the reconciliation...")
    if followup:
        with st.spinner("Thinking..."):
            call_claude(followup)
        st.rerun()
else:
    st.chat_input("Analyze your data first using the sidebar →", disabled=True)
