import os
import sys
import json
import uuid
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.graph_objects as go
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
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }

    .stApp { background-color: #0f1117; color: #e2e8f0; }

    [data-testid="stSidebar"] {
        background-color: #161b27;
        border-right: 1px solid #2d3748;
    }

    .app-header {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
        border-bottom: 1px solid #2d3748;
        margin-bottom: 1.5rem;
    }
    .app-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.6rem;
        font-weight: 600;
        color: #4fd1c5;
    }
    .app-subtitle { font-size: 13px; color: #718096; margin-top: 4px; }

    .sidebar-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        color: #4fd1c5;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin: 16px 0 8px 0;
    }

    .metric-card {
        background: #161b27;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.8rem;
        font-weight: 600;
        color: #4fd1c5;
    }
    .metric-label {
        font-size: 11px;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 4px;
    }
    .metric-card.red .metric-value { color: #fc8181; }
    .metric-card.green .metric-value { color: #68d391; }
    .metric-card.yellow .metric-value { color: #f6ad55; }

    .msg-user {
        background: #1e2a3a;
        border: 1px solid #2d3748;
        border-radius: 12px 12px 2px 12px;
        padding: 14px 18px;
        margin: 12px 0;
        margin-left: 15%;
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
        font-size: 14px;
        line-height: 1.6;
    }
    .label-user {
        font-size: 11px; color: #718096; text-align: right;
        margin-bottom: 4px; font-family: 'IBM Plex Mono', monospace;
    }
    .label-bot {
        font-size: 11px; color: #4fd1c5;
        margin-bottom: 4px; font-family: 'IBM Plex Mono', monospace;
    }

    .section-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        font-weight: 600;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 24px 0 12px 0;
        padding-bottom: 6px;
        border-bottom: 1px solid #2d3748;
    }

    .badge-ready {
        display: inline-block; background: #1a2e1a; color: #68d391;
        border: 1px solid #276749; border-radius: 4px;
        font-size: 11px; font-family: 'IBM Plex Mono', monospace;
        padding: 2px 8px; margin-top: 4px;
    }
    .badge-empty {
        display: inline-block; background: #2d2010; color: #f6ad55;
        border: 1px solid #744210; border-radius: 4px;
        font-size: 11px; font-family: 'IBM Plex Mono', monospace;
        padding: 2px 8px; margin-top: 4px;
    }
    .badge-mapped {
        display: inline-block; background: #1a2040; color: #76e4f7;
        border: 1px solid #2c5282; border-radius: 4px;
        font-size: 11px; font-family: 'IBM Plex Mono', monospace;
        padding: 2px 8px; margin-top: 4px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #4fd1c5, #38b2ac);
        color: #0f1117; border: none; border-radius: 6px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600; font-size: 13px;
        letter-spacing: 0.05em; padding: 10px 0;
        width: 100%; cursor: pointer;
    }
    .stButton > button:hover { opacity: 0.85; color: #0f1117; }

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

    .session-item {
        background: #161b27;
        border: 1px solid #2d3748;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 12px;
        font-family: 'IBM Plex Mono', monospace;
        color: #a0aec0;
        cursor: pointer;
    }

    .welcome-box {
        text-align: center; padding: 4rem 2rem; color: #4a5568;
    }
    .welcome-icon { font-size: 3rem; margin-bottom: 1rem; }
    .welcome-text { font-size: 15px; line-height: 1.8; max-width: 420px; margin: 0 auto; }

    /* Dataframe styling */
    .stDataFrame { border: 1px solid #2d3748; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)


# ── Constants ──────────────────────────────────────────────────────────────────
SESSIONS_FILE = "reconciliation_sessions.json"

SYSTEM_PROMPT = """
You are FinReconcile, a senior financial reconciliation analyst with 15 years
of experience at Big 4 accounting firms.

You will receive pre-computed reconciliation results from a pandas analysis.
The hard math is already done — your job is to explain, interpret, and advise.

WHEN GIVEN RECONCILIATION RESULTS:
1. Summarize the overall picture in 2 sentences (match rate, total exposure)
2. For each mismatch, explain the most likely root cause from this list:
   - Timing difference (payment recorded on different dates)
   - Manual entry error (typo in amount or ID)
   - Payment method mismatch (paid via wire/check, not through system)
   - System sync failure (integration didn't fire)
   - Partial payment (customer paid less than invoiced)
   - Duplicate entry (same transaction recorded twice)
   - Missing record (transaction exists in one system only)
3. For each mismatch, give ONE specific action the finance team should take
4. End with a priority list: what to fix today vs this week vs this month

FOLLOW-UP QUESTIONS:
- Always reference specific IDs and amounts from the data
- Never ask the user to re-paste data already in the conversation
- Give concrete, actionable answers — not generic advice
- If asked to summarize for a CFO, keep it to 3 bullet points maximum

TONE: Direct, precise. You are talking to a Controller or CFO
who has zero tolerance for vague answers.
"""


# ── Session persistence ────────────────────────────────────────────────────────
def load_sessions() -> dict:
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_session(session_id: str, session_data: dict):
    sessions = load_sessions()
    sessions[session_id] = session_data
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2, default=str)


# ── AI column mapping ──────────────────────────────────────────────────────────
def map_columns_with_ai(client: Anthropic, columns_a: list, columns_b: list,
                         label_a: str, label_b: str) -> dict:
    """Ask Claude to map columns from both CSVs to a standard schema."""
    prompt = f"""I have two financial CSV files that need to be reconciled.

{label_a} columns: {columns_a}
{label_b} columns: {columns_b}

Map each file's columns to this standard schema:
- id: the unique identifier (invoice number, transaction ID, reference number, etc.)
- amount: the monetary value
- date: the transaction or invoice date
- name: the customer, vendor, or counterparty name (if available)

Respond ONLY with a valid JSON object in exactly this format, no other text:
{{
  "source_a": {{"id": "col_name", "amount": "col_name", "date": "col_name_or_null", "name": "col_name_or_null"}},
  "source_b": {{"id": "col_name", "amount": "col_name", "date": "col_name_or_null", "name": "col_name_or_null"}}
}}

Use null (not "null") if a column for that field doesn't exist.
Only use column names that actually exist in the lists provided."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Pandas reconciliation engine ───────────────────────────────────────────────
def reconcile_dataframes(df_a: pd.DataFrame, df_b: pd.DataFrame,
                          mapping: dict, label_a: str, label_b: str) -> dict:
    """
    Programmatically compare two dataframes using pandas.
    Returns structured reconciliation results.
    """
    # Rename columns to standard schema
    rename_a = {v: k for k, v in mapping["source_a"].items() if v}
    rename_b = {v: k for k, v in mapping["source_b"].items() if v}

    df_a = df_a.rename(columns=rename_a)
    df_b = df_b.rename(columns=rename_b)

    # Keep only mapped columns
    cols_a = [c for c in ["id", "amount", "date", "name"] if c in df_a.columns]
    cols_b = [c for c in ["id", "amount", "date", "name"] if c in df_b.columns]
    df_a = df_a[cols_a].copy()
    df_b = df_b[cols_b].copy()

    # Normalize id column
    df_a["id"] = df_a["id"].astype(str).str.strip()
    df_b["id"] = df_b["id"].astype(str).str.strip()

    # Normalize amount columns to float
    for df in [df_a, df_b]:
        if "amount" in df.columns:
            df["amount"] = (
                df["amount"].astype(str)
                .str.replace(r"[$,\s]", "", regex=True)
                .astype(float)
            )

    # Merge on ID
    merged = pd.merge(df_a, df_b, on="id", how="outer",
                      suffixes=(f"_{label_a}", f"_{label_b}"))

    results = {
        "matched": [],
        "amount_mismatch": [],
        "date_mismatch": [],
        "missing_in_b": [],
        "missing_in_a": [],
        "summary": {}
    }

    for _, row in merged.iterrows():
        record_id = row["id"]
        amt_a_col = f"amount_{label_a}"
        amt_b_col = f"amount_{label_b}"

        amt_a = row.get(amt_a_col, None)
        amt_b = row.get(amt_b_col, None)

        # Missing in B
        if pd.isna(amt_b):
            results["missing_in_b"].append({
                "id": record_id,
                "amount": float(amt_a) if not pd.isna(amt_a) else 0,
                "source": label_a
            })
            continue

        # Missing in A
        if pd.isna(amt_a):
            results["missing_in_a"].append({
                "id": record_id,
                "amount": float(amt_b) if not pd.isna(amt_b) else 0,
                "source": label_b
            })
            continue

        # Amount mismatch
        if abs(float(amt_a) - float(amt_b)) > 0.01:
            results["amount_mismatch"].append({
                "id": record_id,
                f"amount_{label_a}": float(amt_a),
                f"amount_{label_b}": float(amt_b),
                "difference": round(float(amt_a) - float(amt_b), 2)
            })
            continue

        # Date mismatch (if date column available)
        date_a_col = f"date_{label_a}"
        date_b_col = f"date_{label_b}"
        if date_a_col in row and date_b_col in row:
            if str(row[date_a_col]) != str(row[date_b_col]) and \
               not pd.isna(row[date_a_col]) and not pd.isna(row[date_b_col]):
                results["date_mismatch"].append({
                    "id": record_id,
                    "amount": float(amt_a),
                    f"date_{label_a}": str(row[date_a_col]),
                    f"date_{label_b}": str(row[date_b_col])
                })
                continue

        # Perfect match
        results["matched"].append({"id": record_id, "amount": float(amt_a)})

    # Summary stats
    total = len(merged)
    matched = len(results["matched"])
    mismatched = total - matched
    total_exposure = (
        sum(abs(r["difference"]) for r in results["amount_mismatch"]) +
        sum(r["amount"] for r in results["missing_in_a"]) +
        sum(r["amount"] for r in results["missing_in_b"])
    )

    results["summary"] = {
        "total_records": total,
        "matched": matched,
        "mismatched": mismatched,
        "match_rate": round((matched / total * 100), 1) if total > 0 else 0,
        "total_exposure": round(total_exposure, 2),
        "amount_mismatches": len(results["amount_mismatch"]),
        "date_mismatches": len(results["date_mismatch"]),
        "missing_in_b": len(results["missing_in_b"]),
        "missing_in_a": len(results["missing_in_a"])
    }

    return results


def build_reconciliation_prompt(results: dict, label_a: str, label_b: str) -> str:
    """Convert pandas results into a structured prompt for Claude."""
    s = results["summary"]

    lines = [
        f"RECONCILIATION RESULTS: {label_a} vs {label_b}",
        f"",
        f"SUMMARY:",
        f"- Total records: {s['total_records']}",
        f"- Matched: {s['matched']} ({s['match_rate']}%)",
        f"- Mismatched: {s['mismatched']}",
        f"- Total financial exposure: ${s['total_exposure']:,.2f}",
        f""
    ]

    if results["amount_mismatch"]:
        lines.append("AMOUNT MISMATCHES:")
        for r in sorted(results["amount_mismatch"],
                        key=lambda x: abs(x["difference"]), reverse=True):
            a_key = [k for k in r if k.startswith("amount_") and label_a in k][0]
            b_key = [k for k in r if k.startswith("amount_") and label_b in k][0]
            lines.append(
                f"  - {r['id']}: {label_a}=${r[a_key]:,.2f} vs "
                f"{label_b}=${r[b_key]:,.2f} "
                f"(difference: ${r['difference']:+,.2f})"
            )

    if results["missing_in_b"]:
        lines.append(f"\nMISSING IN {label_b.upper()}:")
        for r in sorted(results["missing_in_b"],
                        key=lambda x: x["amount"], reverse=True):
            lines.append(f"  - {r['id']}: ${r['amount']:,.2f} (in {label_a} only)")

    if results["missing_in_a"]:
        lines.append(f"\nMISSING IN {label_a.upper()}:")
        for r in sorted(results["missing_in_a"],
                        key=lambda x: x["amount"], reverse=True):
            lines.append(f"  - {r['id']}: ${r['amount']:,.2f} (in {label_b} only)")

    if results["date_mismatch"]:
        lines.append(f"\nDATE DISCREPANCIES (amounts match):")
        for r in results["date_mismatch"]:
            date_a = [v for k, v in r.items() if k.startswith("date_") and label_a in k][0]
            date_b = [v for k, v in r.items() if k.startswith("date_") and label_b in k][0]
            lines.append(
                f"  - {r['id']}: ${r['amount']:,.2f} | "
                f"{label_a}={date_a} vs {label_b}={date_b}"
            )

    lines.append(
        f"\nPlease explain each mismatch, identify the most likely root cause, "
        f"and give the finance team a clear action plan prioritized by dollar impact."
    )

    return "\n".join(lines)


def results_to_dataframe(results: dict, label_a: str, label_b: str) -> pd.DataFrame:
    """Convert reconciliation results to a downloadable dataframe."""
    rows = []

    for r in results["matched"]:
        rows.append({"id": r["id"], "status": "✅ Match",
                     f"amount_{label_a}": r["amount"],
                     f"amount_{label_b}": r["amount"], "difference": 0})

    for r in results["amount_mismatch"]:
        a_key = [k for k in r if k.startswith("amount_") and label_a in k][0]
        b_key = [k for k in r if k.startswith("amount_") and label_b in k][0]
        rows.append({"id": r["id"], "status": "❌ Amount Mismatch",
                     f"amount_{label_a}": r[a_key],
                     f"amount_{label_b}": r[b_key],
                     "difference": r["difference"]})

    for r in results["missing_in_b"]:
        rows.append({"id": r["id"], f"status": f"❌ Missing in {label_b}",
                     f"amount_{label_a}": r["amount"],
                     f"amount_{label_b}": None, "difference": r["amount"]})

    for r in results["missing_in_a"]:
        rows.append({"id": r["id"], f"status": f"❌ Missing in {label_a}",
                     f"amount_{label_a}": None,
                     f"amount_{label_b}": r["amount"],
                     "difference": -r["amount"]})

    for r in results["date_mismatch"]:
        rows.append({"id": r["id"], "status": "⚠️ Date Mismatch",
                     f"amount_{label_a}": r["amount"],
                     f"amount_{label_b}": r["amount"], "difference": 0})

    return pd.DataFrame(rows)


def render_pie_charts(recon_df: pd.DataFrame, label_a: str, label_b: str):
    """Render two donut pie charts side by side from the reconciliation dataframe."""
    amt_a_col = [c for c in recon_df.columns if c.startswith("amount_") and label_a in c]
    amt_b_col = [c for c in recon_df.columns if c.startswith("amount_") and label_b in c]

    if not amt_a_col or not amt_b_col:
        st.warning("Could not find amount columns to chart.")
        return

    df_pie = recon_df[["id", amt_a_col[0], amt_b_col[0]]].copy()
    df_a_pie = df_pie[df_pie[amt_a_col[0]].notna()][["id", amt_a_col[0]]]
    df_b_pie = df_pie[df_pie[amt_b_col[0]].notna()][["id", amt_b_col[0]]]

    pie_colors = ["#4fd1c5", "#76e4f7", "#f6ad55", "#fc8181", "#68d391", "#b794f4"]
    chart_layout = dict(
        paper_bgcolor="#161b27",
        plot_bgcolor="#161b27",
        font=dict(color="#e2e8f0", family="IBM Plex Sans"),
        legend=dict(font=dict(color="#a0aec0", size=11)),
        margin=dict(t=50, b=20, l=20, r=20),
        height=340
    )

    pie_col1, pie_col2 = st.columns(2)

    with pie_col1:
        fig_a = go.Figure(data=[go.Pie(
            labels=df_a_pie["id"].tolist(),
            values=df_a_pie[amt_a_col[0]].tolist(),
            hole=0.4,
            marker=dict(colors=pie_colors),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>"
        )])
        fig_a.update_layout(
            title=dict(text=f"{label_a} — Amount by Invoice",
                       font=dict(color="#4fd1c5", size=14), x=0.5),
            **chart_layout
        )
        st.plotly_chart(fig_a, use_container_width=True)

    with pie_col2:
        fig_b = go.Figure(data=[go.Pie(
            labels=df_b_pie["id"].tolist(),
            values=df_b_pie[amt_b_col[0]].tolist(),
            hole=0.4,
            marker=dict(colors=pie_colors),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>"
        )])
        fig_b.update_layout(
            title=dict(text=f"{label_b} — Amount by Invoice",
                       font=dict(color="#4fd1c5", size=14), x=0.5),
            **chart_layout
        )
        st.plotly_chart(fig_b, use_container_width=True)


def is_chart_request(text: str) -> bool:
    """Detect if the user is asking for a chart or visualization."""
    keywords = ["pie", "chart", "graph", "visual", "plot", "diagram",
                "piechart", "pie chart", "show me", "visualize", "visualise"]
    text_lower = text.lower()
    return any(k in text_lower for k in keywords)


# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "client" not in st.session_state:
    st.session_state.client = Anthropic()
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "recon_results" not in st.session_state:
    st.session_state.recon_results = None
if "recon_df" not in st.session_state:
    st.session_state.recon_df = None
if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "show_pie_charts" not in st.session_state:
    st.session_state.show_pie_charts = False


# ── Helper: call Claude ────────────────────────────────────────────────────────
def call_claude(user_message: str) -> str:
    st.session_state.messages.append({"role": "user", "content": user_message})
    response = st.session_state.client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=st.session_state.messages
    )
    reply = response.content[0].text
    st.session_state.messages.append({"role": "assistant", "content": reply})
    return reply


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:1.1rem;font-weight:600;color:#4fd1c5;">💰 FinReconcile</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#718096;">Phase 3 — CSV Upload + AI Analysis</div>', unsafe_allow_html=True)

    st.divider()

    # Source A
    st.markdown('<div class="sidebar-header">📂 Source A</div>', unsafe_allow_html=True)
    label_a = st.text_input("Label", value="Stripe", key="label_a")
    file_a = st.file_uploader("Upload CSV", type=["csv"], key="file_a")
    if file_a:
        df_a_preview = pd.read_csv(file_a)
        file_a.seek(0)
        st.markdown(f'<span class="badge-mapped">✓ {len(df_a_preview)} rows · {len(df_a_preview.columns)} cols</span>', unsafe_allow_html=True)
        with st.expander("Preview", expanded=False):
            st.dataframe(df_a_preview.head(3), use_container_width=True)

    # Source B
    st.markdown('<div class="sidebar-header">📂 Source B</div>', unsafe_allow_html=True)
    label_b = st.text_input("Label", value="QuickBooks", key="label_b")
    file_b = st.file_uploader("Upload CSV", type=["csv"], key="file_b")
    if file_b:
        df_b_preview = pd.read_csv(file_b)
        file_b.seek(0)
        st.markdown(f'<span class="badge-mapped">✓ {len(df_b_preview)} rows · {len(df_b_preview.columns)} cols</span>', unsafe_allow_html=True)
        with st.expander("Preview", expanded=False):
            st.dataframe(df_b_preview.head(3), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    both_uploaded = file_a is not None and file_b is not None
    if both_uploaded:
        st.markdown('<span class="badge-ready">✓ Both files ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-empty">⚠ Upload both CSV files</span>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_clicked = st.button("🔍 Analyze Mismatches", disabled=not both_uploaded)

    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    reset_clicked = st.button("↺ Reset Session")
    st.markdown('</div>', unsafe_allow_html=True)

    # Past sessions
    st.divider()
    st.markdown('<div class="sidebar-header">🗂 Past Sessions</div>', unsafe_allow_html=True)
    sessions = load_sessions()
    if sessions:
        for sid, sdata in sorted(sessions.items(),
                                  key=lambda x: x[1].get("timestamp", ""),
                                  reverse=True)[:5]:
            st.markdown(
                f'<div class="session-item">📄 {sdata.get("label_a","?")} vs '
                f'{sdata.get("label_b","?")}<br>'
                f'<span style="color:#4a5568">{sdata.get("timestamp","")[:16]} · '
                f'{sdata.get("summary",{}).get("match_rate","?")}% match</span></div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown('<div style="font-size:12px;color:#4a5568;font-family:IBM Plex Mono,monospace;">No sessions yet</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="font-size:11px;color:#4a5568;font-family:IBM Plex Mono,monospace;">Model: claude-sonnet-4-6</div>', unsafe_allow_html=True)


# ── Handle reset ───────────────────────────────────────────────────────────────
if reset_clicked:
    for key in ["messages", "analysis_done", "recon_results",
                "recon_df", "column_mapping", "show_pie_charts"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.session_id = str(uuid.uuid4())[:8]
    st.rerun()


# ── Main panel ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-title">FinReconcile</div>
    <div class="app-subtitle">Upload two financial CSVs → AI maps columns → Pandas finds mismatches → Claude explains</div>
</div>
""", unsafe_allow_html=True)


# ── Handle Analyze ─────────────────────────────────────────────────────────────
if analyze_clicked and both_uploaded:
    file_a.seek(0)
    file_b.seek(0)
    df_a = pd.read_csv(file_a)
    df_b = pd.read_csv(file_b)

    with st.spinner("🤖 AI is mapping your columns..."):
        try:
            mapping = map_columns_with_ai(
                st.session_state.client,
                list(df_a.columns), list(df_b.columns),
                label_a, label_b
            )
            st.session_state.column_mapping = mapping
        except Exception as e:
            st.error(f"Column mapping failed: {e}")
            st.stop()

    with st.spinner("📊 Running reconciliation..."):
        results = reconcile_dataframes(df_a, df_b, mapping, label_a, label_b)
        st.session_state.recon_results = results
        st.session_state.recon_df = results_to_dataframe(results, label_a, label_b)

    with st.spinner("💬 Generating analysis..."):
        prompt = build_reconciliation_prompt(results, label_a, label_b)
        call_claude(prompt)
        st.session_state.analysis_done = True

    # Save session to JSON
    save_session(st.session_state.session_id, {
        "timestamp": datetime.now().isoformat(),
        "label_a": label_a,
        "label_b": label_b,
        "column_mapping": mapping,
        "summary": results["summary"],
        "session_id": st.session_state.session_id
    })

    st.rerun()


# ── Dashboard ──────────────────────────────────────────────────────────────────
if st.session_state.analysis_done and st.session_state.recon_results:
    s = st.session_state.recon_results["summary"]

    st.markdown('<div class="section-title">📊 Dashboard</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        color = "green" if s["match_rate"] >= 80 else "yellow" if s["match_rate"] >= 50 else "red"
        st.markdown(f'<div class="metric-card {color}"><div class="metric-value">{s["match_rate"]}%</div><div class="metric-label">Match Rate</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card red"><div class="metric-value">${s["total_exposure"]:,.0f}</div><div class="metric-label">Total Exposure</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{s["matched"]}/{s["total_records"]}</div><div class="metric-label">Records Matched</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card yellow"><div class="metric-value">{s["mismatched"]}</div><div class="metric-label">Issues Found</div></div>', unsafe_allow_html=True)

    # Breakdown bar chart
    st.markdown('<div class="section-title">🔍 Mismatch Breakdown</div>', unsafe_allow_html=True)

    breakdown_data = {
        "Type": ["Amount Mismatch", f"Missing in {label_b}", f"Missing in {label_a}", "Date Mismatch"],
        "Count": [s["amount_mismatches"], s["missing_in_b"], s["missing_in_a"], s["date_mismatches"]]
    }
    breakdown_df = pd.DataFrame(breakdown_data)
    breakdown_df = breakdown_df[breakdown_df["Count"] > 0]

    if not breakdown_df.empty:
        st.bar_chart(breakdown_df.set_index("Type"), color="#4fd1c5")

    # Full results table
    st.markdown('<div class="section-title">📋 Full Reconciliation Table</div>', unsafe_allow_html=True)
    st.dataframe(
        st.session_state.recon_df,
        use_container_width=True,
        hide_index=True
    )

    # Column mapping info
    if st.session_state.column_mapping:
        with st.expander("🤖 AI Column Mapping Used", expanded=False):
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown(f"**{label_a}**")
                for k, v in st.session_state.column_mapping["source_a"].items():
                    if v:
                        st.markdown(f"`{v}` → `{k}`")
            with col_r:
                st.markdown(f"**{label_b}**")
                for k, v in st.session_state.column_mapping["source_b"].items():
                    if v:
                        st.markdown(f"`{v}` → `{k}`")

    # Download button
    st.markdown('<div class="section-title">⬇️ Export</div>', unsafe_allow_html=True)
    csv_export = st.session_state.recon_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Reconciliation Report (CSV)",
        data=csv_export,
        file_name=f"reconciliation_{label_a}_vs_{label_b}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )


# ── Chat section ───────────────────────────────────────────────────────────────
if st.session_state.messages:
    st.markdown('<div class="section-title">💬 AI Analysis</div>', unsafe_allow_html=True)

    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            if "RECONCILIATION RESULTS:" in msg["content"]:
                continue
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="💰"):
                st.markdown(msg["content"])
                # Render pie charts inline after the chart response message
                is_last = (i == len(st.session_state.messages) - 1)
                if is_last and st.session_state.show_pie_charts and st.session_state.recon_df is not None:
                    render_pie_charts(st.session_state.recon_df, label_a, label_b)

if st.session_state.analysis_done:
    followup = st.chat_input("Ask a follow-up question about the reconciliation...")
    if followup:
        if is_chart_request(followup):
            # Don't send to Claude — render charts from data directly
            st.session_state.messages.append({
                "role": "user", "content": followup
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": "📊 Here are the amount distribution charts for both sources:"
            })
            st.session_state.show_pie_charts = True
        else:
            with st.spinner("Thinking..."):
                call_claude(followup)
        st.rerun()
else:
    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome-box">
            <div class="welcome-icon">📂</div>
            <div class="welcome-text">
                Upload two CSV files in the sidebar and click
                <strong style="color:#4fd1c5;">Analyze Mismatches</strong>.<br><br>
                AI will automatically map your columns, find every discrepancy,
                and explain what your finance team should investigate.
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.chat_input("Upload and analyze your CSVs first →", disabled=True)
