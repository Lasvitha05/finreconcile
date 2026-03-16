import os
import sys
import json
import uuid
import sqlite3
import threading
import time
from datetime import datetime
from io import StringIO, BytesIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinReconcile Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    .stApp { background-color: #0a0e17; color: #e2e8f0; }
    [data-testid="stSidebar"] { background-color: #0f1520; border-right: 1px solid #1e2d3d; }

    .app-header { text-align: center; padding: 1.5rem 0 1rem 0; border-bottom: 1px solid #1e2d3d; margin-bottom: 1.5rem; }
    .app-title { font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 600; color: #4fd1c5; }
    .app-subtitle { font-size: 12px; color: #4a5568; margin-top: 4px; letter-spacing: 0.05em; }

    .section-title {
        font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 600;
        color: #4a6fa5; text-transform: uppercase; letter-spacing: 0.12em;
        margin: 24px 0 12px 0; padding-bottom: 6px; border-bottom: 1px solid #1e2d3d;
    }
    .sidebar-header {
        font-family: 'IBM Plex Mono', monospace; font-size: 10px; font-weight: 600;
        color: #4fd1c5; letter-spacing: 0.12em; text-transform: uppercase; margin: 14px 0 6px 0;
    }

    /* Tool call visualization */
    .tool-call {
        background: #0d1a2a; border: 1px solid #1e3a5f;
        border-left: 3px solid #4a6fa5; border-radius: 4px;
        padding: 10px 14px; margin: 6px 0;
        font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #76a9d4;
    }
    .tool-call .tool-name { color: #4fd1c5; font-weight: 600; }
    .tool-result {
        background: #0a1a0a; border: 1px solid #1a3a1a;
        border-left: 3px solid #2d6a2d; border-radius: 4px;
        padding: 8px 14px; margin: 4px 0 10px 0;
        font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #68d391;
    }

    /* Metric cards */
    .metric-card { background: #0f1520; border: 1px solid #1e2d3d; border-radius: 8px; padding: 16px 20px; text-align: center; }
    .metric-value { font-family: 'IBM Plex Mono', monospace; font-size: 1.7rem; font-weight: 600; color: #4fd1c5; }
    .metric-label { font-size: 11px; color: #4a5568; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px; }
    .metric-card.red .metric-value { color: #fc8181; }
    .metric-card.green .metric-value { color: #68d391; }
    .metric-card.yellow .metric-value { color: #f6ad55; }

    /* Alert cards */
    .alert-card {
        background: #1a0f0f; border: 1px solid #4a1a1a;
        border-left: 3px solid #fc8181; border-radius: 6px;
        padding: 10px 14px; margin: 6px 0; font-size: 12px; color: #feb2b2;
    }
    .alert-card.warning { background: #1a160a; border-color: #4a3a0a; border-left-color: #f6ad55; color: #fbd38d; }
    .alert-card.info { background: #0a1a1a; border-color: #0a3a3a; border-left-color: #4fd1c5; color: #81e6d9; }

    /* Status badges */
    .badge { display: inline-block; border-radius: 4px; font-size: 11px; font-family: 'IBM Plex Mono', monospace; padding: 2px 8px; margin: 2px; }
    .badge-green { background: #1a2e1a; color: #68d391; border: 1px solid #276749; }
    .badge-red { background: #2d1010; color: #fc8181; border: 1px solid #742020; }
    .badge-blue { background: #0a1a2e; color: #76e4f7; border: 1px solid #1a4a6a; }
    .badge-orange { background: #2d1a0a; color: #f6ad55; border: 1px solid #744210; }

    /* Agent thinking */
    .thinking { color: #4a5568; font-style: italic; font-size: 13px; padding: 8px 0; }

    .stButton > button {
        background: linear-gradient(135deg, #4fd1c5, #38b2ac); color: #0a0e17;
        border: none; border-radius: 6px; font-family: 'IBM Plex Mono', monospace;
        font-weight: 600; font-size: 12px; letter-spacing: 0.05em;
        padding: 10px 0; width: 100%;
    }
    .stButton > button:hover { opacity: 0.85; color: #0a0e17; }
    .reset-btn > button { background: transparent !important; color: #e53e3e !important; border: 1px solid #e53e3e !important; margin-top: 6px; }
    .reset-btn > button:hover { background: #e53e3e !important; color: white !important; opacity: 1 !important; }

    .schedule-active { color: #68d391; font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
    .schedule-inactive { color: #4a5568; font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
</style>
""", unsafe_allow_html=True)


# ── Constants ──────────────────────────────────────────────────────────────────
DB_PATH = "finreconcile_agent.db"
MAX_AGENT_ITERATIONS = 10

SYSTEM_PROMPT = """
You are FinReconcile Agent — an autonomous financial reconciliation AI with
access to live data sources and analysis tools.

You have tools to:
- Fetch financial data directly from AWS S3 buckets
- Query a local SQLite database for historical records
- Run programmatic reconciliation between two datasets
- Detect anomalies in financial data
- Generate executive summary reports

BEHAVIOR:
- Always fetch fresh data before reconciling — never assume data is current
- After reconciling, always run anomaly detection on the results
- When you find anomalies, explain them clearly with dollar impact
- Prioritize findings by financial exposure (largest dollar amounts first)
- Be autonomous — complete multi-step tasks without asking for confirmation
  unless you genuinely need information you cannot find

RESPONSE FORMAT:
- Use structured output: tables for data, numbered lists for action items
- Always include: total records, match rate, net exposure, top 3 action items
- For executive summaries: max 5 bullet points, CFO-ready language
- Reference specific IDs and amounts — never speak in generalities

TONE: You are a senior analyst. Direct, precise, no filler words.
"""


# ── Database setup ─────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation_runs (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            source_a TEXT,
            source_b TEXT,
            total_records INTEGER,
            matched INTEGER,
            match_rate REAL,
            total_exposure REAL,
            results_json TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id TEXT PRIMARY KEY,
            run_id TEXT,
            timestamp TEXT,
            severity TEXT,
            invoice_id TEXT,
            description TEXT,
            amount REAL,
            FOREIGN KEY (run_id) REFERENCES reconciliation_runs(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS financial_records (
            id TEXT PRIMARY KEY,
            source TEXT,
            invoice_id TEXT,
            amount REAL,
            date TEXT,
            name TEXT,
            ingested_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT,
            source_a TEXT,
            source_b TEXT,
            messages_json TEXT,
            summary_json TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_run_to_db(run_id: str, source_a: str, source_b: str, results: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    s = results["summary"]
    c.execute("""
        INSERT OR REPLACE INTO reconciliation_runs
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id, datetime.now().isoformat(),
        source_a, source_b,
        s["total_records"], s["matched"],
        s["match_rate"], s["total_exposure"],
        json.dumps(results)
    ))
    conn.commit()
    conn.close()


def save_anomalies_to_db(run_id: str, anomalies: list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for a in anomalies:
        c.execute("""
            INSERT OR REPLACE INTO anomalies VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), run_id,
            datetime.now().isoformat(),
            a["severity"], a["invoice_id"],
            a["description"], a["amount"]
        ))
    conn.commit()
    conn.close()


def get_recent_runs(limit: int = 5) -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, timestamp, source_a, source_b, match_rate, total_exposure
        FROM reconciliation_runs
        ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_recent_anomalies(limit: int = 10) -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT severity, invoice_id, description, amount, timestamp
        FROM anomalies
        ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def save_conversation(run_id: str, source_a: str, source_b: str,
                      messages: list, summary: dict):
    """Save full conversation + run summary to SQLite."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO conversations
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        datetime.now().isoformat(),
        source_a, source_b,
        json.dumps(messages),
        json.dumps(summary)
    ))
    conn.commit()
    conn.close()


def get_saved_conversations(limit: int = 8) -> list:
    """Retrieve recent conversations from SQLite for sidebar display."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT run_id, timestamp, source_a, source_b, summary_json
        FROM conversations
        ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def load_conversation(run_id: str) -> dict:
    """Load a full conversation by run_id."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT run_id, source_a, source_b, messages_json, summary_json
        FROM conversations WHERE run_id = ?
    """, (run_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "run_id": row[0],
        "source_a": row[1],
        "source_b": row[2],
        "messages": json.loads(row[3]),
        "summary": json.loads(row[4])
    }


def query_db_tool(query: str) -> str:
    """Execute a read-only SQL query on the local database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty:
            return "Query returned no results."
        return df.to_string(index=False)
    except Exception as e:
        return f"Database query error: {str(e)}"


# ── AWS S3 helpers ─────────────────────────────────────────────────────────────
def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )


def fetch_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """Fetch a CSV or Parquet file from S3 and return as DataFrame."""
    s3 = get_s3_client()
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read()

    if key.endswith(".parquet"):
        return pd.read_parquet(BytesIO(body))
    else:
        return pd.read_csv(StringIO(body.decode("utf-8")))


def list_s3_files(bucket: str, prefix: str = "") -> list:
    """List files in an S3 bucket with optional prefix."""
    s3 = get_s3_client()
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if "Contents" not in response:
        return []
    return [obj["Key"] for obj in response["Contents"]]


# ── Reconciliation engine (reused from Phase 3) ────────────────────────────────
def map_columns_with_ai(client, cols_a, cols_b, label_a, label_b) -> dict:
    prompt = f"""You are mapping financial CSV columns to a standard reconciliation schema.

{label_a} columns: {cols_a}
{label_b} columns: {cols_b}

Standard schema fields:
- id: the SHARED business identifier used to JOIN both datasets — must be the
  same type of reference in both files (e.g. invoice number, transaction ref).
  IMPORTANT: if one file has both a system ID (like payment_id, py_xxxxx) AND
  a business reference (like invoice_ref, INV-xxxxx), always prefer the
  business reference as the id because it will match across systems.
- amount: the monetary value
- date: the transaction or invoice date
- name: the customer or counterparty name

Critical rule: the id field must be the column whose VALUES will actually
match between the two files. Pick the column that looks like a shared
invoice or reference number, not an internal system ID.

Respond ONLY with valid JSON, no other text:
{{
  "source_a": {{"id": "col", "amount": "col", "date": "col_or_null", "name": "col_or_null"}},
  "source_b": {{"id": "col", "amount": "col", "date": "col_or_null", "name": "col_or_null"}}
}}
Use null (not the string "null") if a field has no matching column."""

    r = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = r.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def reconcile_dataframes(df_a, df_b, mapping, label_a, label_b) -> dict:
    rename_a = {v: k for k, v in mapping["source_a"].items() if v}
    rename_b = {v: k for k, v in mapping["source_b"].items() if v}
    df_a = df_a.rename(columns=rename_a)
    df_b = df_b.rename(columns=rename_b)
    cols_a = [c for c in ["id", "amount", "date", "name"] if c in df_a.columns]
    cols_b = [c for c in ["id", "amount", "date", "name"] if c in df_b.columns]
    df_a = df_a[cols_a].copy()
    df_b = df_b[cols_b].copy()
    df_a["id"] = df_a["id"].astype(str).str.strip()
    df_b["id"] = df_b["id"].astype(str).str.strip()
    for df in [df_a, df_b]:
        if "amount" in df.columns:
            df["amount"] = df["amount"].astype(str).str.replace(r"[$,\s]", "", regex=True).astype(float)

    merged = pd.merge(df_a, df_b, on="id", how="outer", suffixes=(f"_{label_a}", f"_{label_b}"))
    results = {"matched": [], "amount_mismatch": [], "date_mismatch": [], "missing_in_b": [], "missing_in_a": []}

    for _, row in merged.iterrows():
        rid = row["id"]
        amt_a = row.get(f"amount_{label_a}", None)
        amt_b = row.get(f"amount_{label_b}", None)
        if pd.isna(amt_b):
            results["missing_in_b"].append({"id": rid, "amount": float(amt_a) if not pd.isna(amt_a) else 0})
        elif pd.isna(amt_a):
            results["missing_in_a"].append({"id": rid, "amount": float(amt_b) if not pd.isna(amt_b) else 0})
        elif abs(float(amt_a) - float(amt_b)) > 0.01:
            results["amount_mismatch"].append({
                "id": rid,
                f"amount_{label_a}": float(amt_a),
                f"amount_{label_b}": float(amt_b),
                "difference": round(float(amt_a) - float(amt_b), 2)
            })
        else:
            date_a = row.get(f"date_{label_a}")
            date_b = row.get(f"date_{label_b}")
            if date_a and date_b and str(date_a) != str(date_b) and not pd.isna(date_a) and not pd.isna(date_b):
                results["date_mismatch"].append({"id": rid, "amount": float(amt_a),
                    f"date_{label_a}": str(date_a), f"date_{label_b}": str(date_b)})
            else:
                results["matched"].append({"id": rid, "amount": float(amt_a)})

    total = len(merged)
    matched = len(results["matched"])
    exposure = (
        sum(abs(r["difference"]) for r in results["amount_mismatch"]) +
        sum(r["amount"] for r in results["missing_in_a"]) +
        sum(r["amount"] for r in results["missing_in_b"])
    )
    results["summary"] = {
        "total_records": total, "matched": matched,
        "mismatched": total - matched,
        "match_rate": round(matched / total * 100, 1) if total > 0 else 0,
        "total_exposure": round(exposure, 2),
        "amount_mismatches": len(results["amount_mismatch"]),
        "date_mismatches": len(results["date_mismatch"]),
        "missing_in_b": len(results["missing_in_b"]),
        "missing_in_a": len(results["missing_in_a"])
    }
    return results


def detect_anomalies(results: dict, label_a: str, label_b: str) -> list:
    """Detect anomalies in reconciliation results and classify by severity."""
    anomalies = []

    # Large amount mismatches → HIGH
    for r in results["amount_mismatch"]:
        diff = abs(r["difference"])
        severity = "HIGH" if diff > 1000 else "MEDIUM" if diff > 100 else "LOW"
        anomalies.append({
            "severity": severity,
            "invoice_id": r["id"],
            "description": f"Amount mismatch of ${diff:,.2f} between {label_a} and {label_b}",
            "amount": diff
        })

    # Missing records → HIGH if > $500
    for r in results["missing_in_b"]:
        severity = "HIGH" if r["amount"] > 500 else "MEDIUM"
        anomalies.append({
            "severity": severity,
            "invoice_id": r["id"],
            "description": f"Record exists in {label_a} (${r['amount']:,.2f}) but missing in {label_b}",
            "amount": r["amount"]
        })

    for r in results["missing_in_a"]:
        severity = "HIGH" if r["amount"] > 500 else "MEDIUM"
        anomalies.append({
            "severity": severity,
            "invoice_id": r["id"],
            "description": f"Record exists in {label_b} (${r['amount']:,.2f}) but missing in {label_a}",
            "amount": r["amount"]
        })

    # Date mismatches → LOW (amounts match, timing difference)
    for r in results["date_mismatch"]:
        anomalies.append({
            "severity": "LOW",
            "invoice_id": r["id"],
            "description": f"Date discrepancy on ${r['amount']:,.2f} record",
            "amount": r["amount"]
        })

    return sorted(anomalies, key=lambda x: (
        {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["severity"]], -x["amount"]
    ))


def results_to_string(results: dict, label_a: str, label_b: str) -> str:
    """Convert reconciliation results to a readable string for Claude."""
    s = results["summary"]
    lines = [
        f"RECONCILIATION: {label_a} vs {label_b}",
        f"Total: {s['total_records']} records | Matched: {s['matched']} ({s['match_rate']}%) | Exposure: ${s['total_exposure']:,.2f}",
        ""
    ]
    if results["amount_mismatch"]:
        lines.append("AMOUNT MISMATCHES:")
        for r in sorted(results["amount_mismatch"], key=lambda x: abs(x["difference"]), reverse=True):
            a_key = [k for k in r if "amount_" in k and label_a in k][0]
            b_key = [k for k in r if "amount_" in k and label_b in k][0]
            lines.append(f"  {r['id']}: {label_a}=${r[a_key]:,.2f} vs {label_b}=${r[b_key]:,.2f} (diff=${r['difference']:+,.2f})")
    if results["missing_in_b"]:
        lines.append(f"MISSING IN {label_b.upper()}:")
        for r in results["missing_in_b"]:
            lines.append(f"  {r['id']}: ${r['amount']:,.2f}")
    if results["missing_in_a"]:
        lines.append(f"MISSING IN {label_a.upper()}:")
        for r in results["missing_in_a"]:
            lines.append(f"  {r['id']}: ${r['amount']:,.2f}")
    if results["date_mismatch"]:
        lines.append("DATE DISCREPANCIES:")
        for r in results["date_mismatch"]:
            lines.append(f"  {r['id']}: ${r['amount']:,.2f}")
    return "\n".join(lines)


# ── Agent tool definitions ─────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "list_s3_files",
        "description": "List available files in an AWS S3 bucket. Use this first to discover what data is available before fetching.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "description": "S3 bucket name"},
                "prefix": {"type": "string", "description": "Optional file prefix/folder path to filter results", "default": ""}
            },
            "required": ["bucket"]
        }
    },
    {
        "name": "fetch_s3_file",
        "description": "Fetch a CSV or Parquet file from AWS S3 and return its contents as a data summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "description": "S3 bucket name"},
                "key": {"type": "string", "description": "Full path to the file in the bucket"},
                "source_label": {"type": "string", "description": "Label for this data source (e.g. 'Stripe', 'QuickBooks')"}
            },
            "required": ["bucket", "key", "source_label"]
        }
    },
    {
        "name": "run_reconciliation",
        "description": "Run a full reconciliation between two datasets that have already been fetched. Returns mismatches ranked by dollar impact.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_a_label": {"type": "string", "description": "Label for source A"},
                "source_b_label": {"type": "string", "description": "Label for source B"}
            },
            "required": ["source_a_label", "source_b_label"]
        }
    },
    {
        "name": "detect_anomalies",
        "description": "Detect and classify anomalies in the latest reconciliation results. Returns HIGH/MEDIUM/LOW severity findings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_a_label": {"type": "string"},
                "source_b_label": {"type": "string"}
            },
            "required": ["source_a_label", "source_b_label"]
        }
    },
    {
        "name": "query_database",
        "description": "Query the local SQLite database for historical reconciliation runs, anomalies, and financial records.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SELECT SQL query to run against the database"}
            },
            "required": ["sql"]
        }
    },
    {
        "name": "generate_report",
        "description": "Generate a formatted executive summary report of the latest reconciliation for CFO/Controller review.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_a_label": {"type": "string"},
                "source_b_label": {"type": "string"},
                "audience": {
                    "type": "string",
                    "enum": ["cfo", "controller", "analyst"],
                    "description": "Target audience determines detail level"
                }
            },
            "required": ["source_a_label", "source_b_label", "audience"]
        }
    }
]


# ── Tool execution ─────────────────────────────────────────────────────────────
def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result as a string."""
    try:
        if tool_name == "list_s3_files":
            files = list_s3_files(tool_input["bucket"], tool_input.get("prefix", ""))
            if not files:
                return f"No files found in s3://{tool_input['bucket']}/{tool_input.get('prefix', '')}"
            return f"Found {len(files)} files:\n" + "\n".join(f"  - {f}" for f in files)

        elif tool_name == "fetch_s3_file":
            df = fetch_from_s3(tool_input["bucket"], tool_input["key"])
            label = tool_input["source_label"]
            st.session_state.fetched_data[label] = df
            return (
                f"Fetched {label} from s3://{tool_input['bucket']}/{tool_input['key']}\n"
                f"Rows: {len(df)} | Columns: {list(df.columns)}\n"
                f"Sample:\n{df.head(3).to_string(index=False)}"
            )

        elif tool_name == "run_reconciliation":
            label_a = tool_input["source_a_label"]
            label_b = tool_input["source_b_label"]
            if label_a not in st.session_state.fetched_data:
                return f"Error: No data fetched for '{label_a}'. Use fetch_s3_file first."
            if label_b not in st.session_state.fetched_data:
                return f"Error: No data fetched for '{label_b}'. Use fetch_s3_file first."

            df_a = st.session_state.fetched_data[label_a]
            df_b = st.session_state.fetched_data[label_b]
            mapping = map_columns_with_ai(
                st.session_state.client,
                list(df_a.columns), list(df_b.columns), label_a, label_b
            )
            results = reconcile_dataframes(df_a, df_b, mapping, label_a, label_b)

            run_id = str(uuid.uuid4())[:8]
            st.session_state.current_results = results
            st.session_state.current_labels = (label_a, label_b)
            st.session_state.current_run_id = run_id
            st.session_state.column_mapping = mapping
            save_run_to_db(run_id, label_a, label_b, results)

            return results_to_string(results, label_a, label_b)

        elif tool_name == "detect_anomalies":
            if not st.session_state.current_results:
                return "No reconciliation results available. Run reconciliation first."
            label_a = tool_input["source_a_label"]
            label_b = tool_input["source_b_label"]
            anomalies = detect_anomalies(
                st.session_state.current_results, label_a, label_b
            )
            st.session_state.current_anomalies = anomalies
            if st.session_state.current_run_id:
                save_anomalies_to_db(st.session_state.current_run_id, anomalies)

            if not anomalies:
                return "No anomalies detected."

            lines = [f"Found {len(anomalies)} anomalies:"]
            for a in anomalies:
                lines.append(f"  [{a['severity']}] {a['invoice_id']}: {a['description']} (${a['amount']:,.2f})")
            return "\n".join(lines)

        elif tool_name == "query_database":
            return query_db_tool(tool_input["sql"])

        elif tool_name == "generate_report":
            if not st.session_state.current_results:
                return "No reconciliation results available. Run reconciliation first."
            results = st.session_state.current_results
            anomalies = st.session_state.current_anomalies or []
            s = results["summary"]
            label_a = tool_input["source_a_label"]
            label_b = tool_input["source_b_label"]
            audience = tool_input["audience"]

            report = [
                f"FINRECONCILE REPORT — {label_a} vs {label_b}",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                f"Audience: {audience.upper()}",
                "─" * 50,
                f"SUMMARY",
                f"  Match Rate:       {s['match_rate']}%",
                f"  Total Records:    {s['total_records']}",
                f"  Matched:          {s['matched']}",
                f"  Issues Found:     {s['mismatched']}",
                f"  Total Exposure:   ${s['total_exposure']:,.2f}",
                "─" * 50,
                f"HIGH SEVERITY ANOMALIES ({len([a for a in anomalies if a['severity']=='HIGH'])})"
            ]
            for a in [x for x in anomalies if x["severity"] == "HIGH"]:
                report.append(f"  ⚠ {a['invoice_id']}: {a['description']}")
            report.append("─" * 50)
            st.session_state.report_ready = "\n".join(report)
            return "\n".join(report)

        else:
            return f"Unknown tool: {tool_name}"

    except NoCredentialsError:
        return "AWS credentials not found. Check your .env file for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
    except ClientError as e:
        return f"AWS error: {e.response['Error']['Message']}"
    except Exception as e:
        return f"Tool execution error: {str(e)}"


# ── Agentic loop ───────────────────────────────────────────────────────────────
def run_agent(user_message: str):
    """
    Core agentic loop. Claude decides which tools to call,
    calls them, checks results, and continues until done.
    Yields (type, content) tuples for streaming to UI.
    """
    st.session_state.messages.append({"role": "user", "content": user_message})
    current_messages = list(st.session_state.messages)

    for iteration in range(MAX_AGENT_ITERATIONS):
        response = st.session_state.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=current_messages
        )

        # Collect text and tool use blocks
        text_parts = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        # Yield text if any
        if text_parts:
            combined_text = "\n".join(text_parts)
            yield ("text", combined_text)

        # If no tool calls, agent is done
        if response.stop_reason == "end_turn" or not tool_calls:
            final_text = "\n".join(text_parts)
            if final_text:
                st.session_state.messages.append({
                    "role": "assistant", "content": final_text
                })
            break

        # Add assistant message with tool use blocks
        current_messages.append({
            "role": "assistant",
            "content": response.content
        })

        # Execute each tool and collect results
        tool_results = []
        for tool_call in tool_calls:
            yield ("tool_call", {"name": tool_call.name, "input": tool_call.input})

            result = execute_tool(tool_call.name, tool_call.input)

            yield ("tool_result", {"name": tool_call.name, "result": result[:500]})

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": result
            })

        # Feed tool results back to Claude
        current_messages.append({
            "role": "user",
            "content": tool_results
        })

    # Mark analysis done and save conversation if we have results
    if st.session_state.current_results:
        st.session_state.analysis_done = True
        labels = st.session_state.current_labels or ("Unknown", "Unknown")
        save_conversation(
            run_id=st.session_state.current_run_id or str(uuid.uuid4())[:8],
            source_a=labels[0],
            source_b=labels[1],
            messages=st.session_state.messages,
            summary=st.session_state.current_results.get("summary", {})
        )


# ── Scheduled reconciliation ───────────────────────────────────────────────────
def scheduled_reconciliation():
    """Background thread that runs reconciliation on a schedule."""
    while st.session_state.get("schedule_active", False):
        interval = st.session_state.get("schedule_interval_mins", 30)
        time.sleep(interval * 60)
        if st.session_state.get("schedule_active", False):
            cfg = st.session_state.get("schedule_config", {})
            if cfg.get("bucket") and cfg.get("key_a") and cfg.get("key_b"):
                st.session_state.schedule_last_run = datetime.now().isoformat()
                st.session_state.pending_schedule_run = True


# ── Session state init ─────────────────────────────────────────────────────────
defaults = {
    "messages": [],
    "fetched_data": {},
    "current_results": None,
    "current_labels": None,
    "current_run_id": None,
    "current_anomalies": None,
    "column_mapping": None,
    "analysis_done": False,
    "report_ready": None,
    "schedule_active": False,
    "schedule_interval_mins": 30,
    "schedule_config": {},
    "schedule_last_run": None,
    "pending_schedule_run": False,
    "show_pie_charts": False,
    "agent_log": [],
    "pending_load_run_id": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "client" not in st.session_state:
    st.session_state.client = Anthropic()

init_db()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:1.1rem;font-weight:600;color:#4fd1c5;">🤖 FinReconcile Agent</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#4a5568;font-family:IBM Plex Mono,monospace;">Phase 4 — Autonomous Agent</div>', unsafe_allow_html=True)

    st.divider()

    # AWS config
    st.markdown('<div class="sidebar-header">☁️ AWS S3 Config</div>', unsafe_allow_html=True)
    bucket_name = st.text_input("Bucket name", placeholder="my-finance-bucket", key="bucket_input")

    col_s3a, col_s3b = st.columns(2)
    with col_s3a:
        key_a = st.text_input("Source A key", placeholder="stripe/jan.csv", key="key_a_input")
        label_a = st.text_input("Label A", value="Stripe", key="label_a_input")
    with col_s3b:
        key_b = st.text_input("Source B key", placeholder="quickbooks/jan.csv", key="key_b_input")
        label_b = st.text_input("Label B", value="QuickBooks", key="label_b_input")

    # Status indicator
    if bucket_name and key_a and key_b:
        st.markdown('<span class="badge badge-green">✓ S3 config ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-orange">⚠ Configure S3 above</span>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick action buttons
    st.markdown('<div class="sidebar-header">⚡ Quick Actions</div>', unsafe_allow_html=True)

    if st.button("🔍 Reconcile Now", disabled=not (bucket_name and key_a and key_b)):
        instruction = (
            f"Fetch the file at key '{key_a}' from bucket '{bucket_name}' as '{label_a}', "
            f"then fetch '{key_b}' from the same bucket as '{label_b}'. "
            f"Run a full reconciliation, detect all anomalies, and give me a complete analysis."
        )
        st.session_state.pending_instruction = instruction

    if st.button("📋 Executive Summary", disabled=not st.session_state.analysis_done):
        st.session_state.pending_instruction = (
            f"Generate an executive summary report for {st.session_state.current_labels[0] if st.session_state.current_labels else 'the last run'} "
            f"vs {st.session_state.current_labels[1] if st.session_state.current_labels else ''} "
            f"for a CFO audience."
        )

    if st.button("🔎 Check Anomaly History"):
        st.session_state.pending_instruction = (
            "Query the database for the 10 most recent HIGH severity anomalies "
            "and summarize the pattern."
        )

    # Scheduler
    st.divider()
    st.markdown('<div class="sidebar-header">⏱ Auto-Scheduler</div>', unsafe_allow_html=True)
    interval = st.selectbox("Run every", [15, 30, 60, 120, 360], index=1, format_func=lambda x: f"{x} mins")
    st.session_state.schedule_interval_mins = interval

    sched_col1, sched_col2 = st.columns(2)
    with sched_col1:
        if st.button("▶ Start"):
            if bucket_name and key_a and key_b:
                st.session_state.schedule_active = True
                st.session_state.schedule_config = {"bucket": bucket_name, "key_a": key_a, "key_b": key_b}
                t = threading.Thread(target=scheduled_reconciliation, daemon=True)
                t.start()
    with sched_col2:
        if st.button("⏹ Stop"):
            st.session_state.schedule_active = False

    if st.session_state.schedule_active:
        st.markdown(f'<div class="schedule-active">● Running every {interval}m</div>', unsafe_allow_html=True)
        if st.session_state.schedule_last_run:
            st.markdown(f'<div style="font-size:10px;color:#4a5568;">Last: {st.session_state.schedule_last_run[:16]}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="schedule-inactive">○ Scheduler off</div>', unsafe_allow_html=True)

    # Past conversations with Load buttons
    st.divider()
    st.markdown('<div class="sidebar-header">🗂 Past Sessions</div>', unsafe_allow_html=True)
    saved = get_saved_conversations(8)
    if saved:
        for row in saved:
            run_id, ts, src_a, src_b, summary_json = row
            try:
                s = json.loads(summary_json)
                match_rate = s.get("match_rate", "?")
                exposure = s.get("total_exposure", 0)
            except:
                match_rate, exposure = "?", 0

            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(
                    f'<div style="font-size:11px;font-family:IBM Plex Mono,monospace;'
                    f'color:#a0aec0;padding:4px 0;">'
                    f'{src_a} vs {src_b}<br>'
                    f'<span style="color:#4a5568;">{ts[:16]} · {match_rate}% · ${exposure:,.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col_btn:
                if st.button("Load", key=f"load_{run_id}"):
                    st.session_state.pending_load_run_id = run_id
    else:
        st.markdown(
            '<div style="font-size:11px;color:#4a5568;font-family:IBM Plex Mono,monospace;">'
            'No saved sessions yet</div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    reset_clicked = st.button("↺ Reset Session")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;color:#4a5568;font-family:IBM Plex Mono,monospace;margin-top:8px;">claude-sonnet-4-6 · tool use</div>', unsafe_allow_html=True)


# ── Handle reset ───────────────────────────────────────────────────────────────
if reset_clicked:
    for k in defaults:
        st.session_state[k] = defaults[k] if not isinstance(defaults[k], dict) else {}
    if "client" in st.session_state:
        pass  # keep client
    st.rerun()


# ── Handle load session ────────────────────────────────────────────────────────
if st.session_state.pending_load_run_id:
    run_id = st.session_state.pending_load_run_id
    st.session_state.pending_load_run_id = None
    data = load_conversation(run_id)
    if data:
        # Restore conversation
        st.session_state.messages = data["messages"]
        st.session_state.current_run_id = data["run_id"]
        st.session_state.current_labels = (data["source_a"], data["source_b"])
        # Restore reconciliation results from DB
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT results_json FROM reconciliation_runs WHERE id = ?", (run_id,))
        row = c.fetchone()
        conn.close()
        if row:
            st.session_state.current_results = json.loads(row[0])
            st.session_state.analysis_done = True
        st.rerun()


# ── Main panel ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-title">FinReconcile Agent</div>
    <div class="app-subtitle">AUTONOMOUS · TOOL-USING · AWS S3 + DATABASE · PROACTIVE ANOMALY DETECTION</div>
</div>
""", unsafe_allow_html=True)


# ── Handle pending scheduled run ───────────────────────────────────────────────
if st.session_state.pending_schedule_run:
    st.session_state.pending_schedule_run = False
    cfg = st.session_state.schedule_config
    st.session_state.pending_instruction = (
        f"Auto-scheduled run: fetch '{cfg['key_a']}' and '{cfg['key_b']}' "
        f"from bucket '{cfg['bucket']}', reconcile, detect anomalies, and alert on any HIGH severity findings."
    )


# ── Dashboard (shown after analysis) ──────────────────────────────────────────
if st.session_state.analysis_done and st.session_state.current_results:
    s = st.session_state.current_results["summary"]
    la, lb = st.session_state.current_labels

    st.markdown('<div class="section-title">📊 Live Dashboard</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    color = "green" if s["match_rate"] >= 80 else "yellow" if s["match_rate"] >= 50 else "red"
    with c1:
        st.markdown(f'<div class="metric-card {color}"><div class="metric-value">{s["match_rate"]}%</div><div class="metric-label">Match Rate</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card red"><div class="metric-value">${s["total_exposure"]:,.0f}</div><div class="metric-label">Exposure</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{s["matched"]}/{s["total_records"]}</div><div class="metric-label">Matched</div></div>', unsafe_allow_html=True)
    with c4:
        high_count = len([a for a in (st.session_state.current_anomalies or []) if a["severity"] == "HIGH"])
        st.markdown(f'<div class="metric-card {"red" if high_count > 0 else "green"}"><div class="metric-value">{high_count}</div><div class="metric-label">High Alerts</div></div>', unsafe_allow_html=True)

    # ── Anomaly Summary Report (replaces wall of individual cards) ────────────
    if st.session_state.current_anomalies:
        anomalies = st.session_state.current_anomalies
        high   = [a for a in anomalies if a["severity"] == "HIGH"]
        medium = [a for a in anomalies if a["severity"] == "MEDIUM"]
        low    = [a for a in anomalies if a["severity"] == "LOW"]
        total_high_exposure = sum(a["amount"] for a in high)

        st.markdown('<div class="section-title">📋 Anomaly Summary Report</div>', unsafe_allow_html=True)

        # Summary row
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.markdown(f'<div class="metric-card red"><div class="metric-value">{len(high)}</div><div class="metric-label">High Severity</div></div>', unsafe_allow_html=True)
        with r2:
            st.markdown(f'<div class="metric-card yellow"><div class="metric-value">{len(medium)}</div><div class="metric-label">Medium Severity</div></div>', unsafe_allow_html=True)
        with r3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(low)}</div><div class="metric-label">Low Severity</div></div>', unsafe_allow_html=True)
        with r4:
            st.markdown(f'<div class="metric-card red"><div class="metric-value">${total_high_exposure:,.0f}</div><div class="metric-label">High Exposure</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Top 5 HIGH issues only — not every single one
        if high:
            st.markdown(
                f'<div class="alert-card">🚨 <b>Top {min(5, len(high))} High Severity Issues</b> '
                f'(${total_high_exposure:,.2f} total exposure across {len(high)} records)</div>',
                unsafe_allow_html=True
            )
            top5 = sorted(high, key=lambda x: x["amount"], reverse=True)[:5]
            rows_h = [{"Invoice": a["invoice_id"], "Issue": a["description"],
                       "Exposure": f'${a["amount"]:,.2f}', "Severity": "🔴 HIGH"} for a in top5]
            st.dataframe(pd.DataFrame(rows_h), use_container_width=True, hide_index=True)
            if len(high) > 5:
                with st.expander(f"View all {len(high)} high severity issues"):
                    all_high = [{"Invoice": a["invoice_id"], "Issue": a["description"],
                                 "Exposure": f'${a["amount"]:,.2f}'} for a in high]
                    st.dataframe(pd.DataFrame(all_high), use_container_width=True, hide_index=True)

        # Medium issues — collapsed by default
        if medium:
            with st.expander(f"⚠️ {len(medium)} Medium Severity Issues — ${sum(a['amount'] for a in medium):,.2f} exposure"):
                rows_m = [{"Invoice": a["invoice_id"], "Issue": a["description"],
                           "Exposure": f'${a["amount"]:,.2f}'} for a in medium]
                st.dataframe(pd.DataFrame(rows_m), use_container_width=True, hide_index=True)

        # Low issues — collapsed by default
        if low:
            with st.expander(f"ℹ️ {len(low)} Low Severity Issues (date discrepancies)"):
                rows_l = [{"Invoice": a["invoice_id"], "Issue": a["description"],
                           "Exposure": f'${a["amount"]:,.2f}'} for a in low]
                st.dataframe(pd.DataFrame(rows_l), use_container_width=True, hide_index=True)

    # Results table
    st.markdown('<div class="section-title">📋 Reconciliation Table</div>', unsafe_allow_html=True)
    results = st.session_state.current_results
    rows = []
    for r in results["matched"]:
        rows.append({"ID": r["id"], la: f'${r["amount"]:,.2f}', lb: f'${r["amount"]:,.2f}', "Status": "✅ Match", "Diff": "$0.00"})
    for r in results["amount_mismatch"]:
        a_key = [k for k in r if "amount_" in k and la in k][0]
        b_key = [k for k in r if "amount_" in k and lb in k][0]
        rows.append({"ID": r["id"], la: f'${r[a_key]:,.2f}', lb: f'${r[b_key]:,.2f}', "Status": "❌ Mismatch", "Diff": f'${r["difference"]:+,.2f}'})
    for r in results["missing_in_b"]:
        rows.append({"ID": r["id"], la: f'${r["amount"]:,.2f}', lb: "—", "Status": f"❌ Missing in {lb}", "Diff": f'${r["amount"]:,.2f}'})
    for r in results["missing_in_a"]:
        rows.append({"ID": r["id"], la: "—", lb: f'${r["amount"]:,.2f}', "Status": f"❌ Missing in {la}", "Diff": f'-${r["amount"]:,.2f}'})
    for r in results["date_mismatch"]:
        rows.append({"ID": r["id"], la: f'${r["amount"]:,.2f}', lb: f'${r["amount"]:,.2f}', "Status": "⚠️ Date Gap", "Diff": "$0.00"})

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Pie charts on demand
    if st.session_state.show_pie_charts:
        st.markdown('<div class="section-title">🥧 Amount Distribution</div>', unsafe_allow_html=True)
        all_rows = pd.DataFrame(rows)
        pie_colors = ["#4fd1c5", "#76e4f7", "#f6ad55", "#fc8181", "#68d391", "#b794f4"]
        pc1, pc2 = st.columns(2)

        def make_pie(df_col, title):
            valid = []
            for _, row in all_rows.iterrows():
                val = str(row[df_col]).replace("$", "").replace(",", "").replace("—", "")
                try:
                    valid.append({"id": row["ID"], "amt": float(val)})
                except:
                    pass
            if not valid:
                return None
            fig = go.Figure(data=[go.Pie(
                labels=[v["id"] for v in valid],
                values=[v["amt"] for v in valid],
                hole=0.4, marker=dict(colors=pie_colors),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>"
            )])
            fig.update_layout(
                title=dict(text=title, font=dict(color="#4fd1c5", size=13), x=0.5),
                paper_bgcolor="#0f1520", plot_bgcolor="#0f1520",
                font=dict(color="#e2e8f0"), height=320,
                margin=dict(t=50, b=10, l=10, r=10)
            )
            return fig

        with pc1:
            fig = make_pie(la, f"{la} Amounts")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        with pc2:
            fig = make_pie(lb, f"{lb} Amounts")
            if fig:
                st.plotly_chart(fig, use_container_width=True)

    # Download
    if rows:
        csv_out = pd.DataFrame(rows).to_csv(index=False)
        st.download_button(
            "📥 Download Report CSV",
            data=csv_out,
            file_name=f"recon_{la}_vs_{lb}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )


# ── Chat / Agent section ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">🤖 Agent Console</div>', unsafe_allow_html=True)

# Welcome state
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center;padding:3rem 2rem;color:#4a5568;">
        <div style="font-size:2.5rem;margin-bottom:1rem;">🤖</div>
        <div style="font-size:14px;line-height:1.8;max-width:500px;margin:0 auto;">
            Configure your S3 bucket in the sidebar, then use <b style="color:#4fd1c5;">Quick Actions</b>
            or type a natural language instruction below.<br><br>
            <span style="font-family:IBM Plex Mono,monospace;font-size:12px;color:#4a6fa5;">
            "Reconcile January data and alert me on anything over $1,000"<br>
            "What anomalies did we find last week?"<br>
            "Generate a CFO summary of the latest run"
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Render conversation
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            if isinstance(msg["content"], str):
                st.markdown(msg["content"])


# ── Handle pending instruction (from sidebar buttons) ─────────────────────────
if "pending_instruction" in st.session_state and st.session_state.pending_instruction:
    instruction = st.session_state.pending_instruction
    st.session_state.pending_instruction = None

    with st.chat_message("user"):
        st.markdown(instruction)

    with st.chat_message("assistant", avatar="🤖"):
        tool_placeholder = st.empty()
        text_placeholder = st.empty()
        collected_text = []

        for event_type, event_data in run_agent(instruction):
            if event_type == "tool_call":
                tool_placeholder.markdown(
                    f'<div class="tool-call">⚙ Calling <span class="tool-name">{event_data["name"]}</span>'
                    f'<br><span style="color:#4a5568;font-size:11px;">{json.dumps(event_data["input"])[:120]}...</span></div>',
                    unsafe_allow_html=True
                )
            elif event_type == "tool_result":
                tool_placeholder.markdown(
                    f'<div class="tool-result">✓ {event_data["name"]} → {event_data["result"][:200]}</div>',
                    unsafe_allow_html=True
                )
            elif event_type == "text":
                collected_text.append(event_data)
                text_placeholder.markdown("\n\n".join(collected_text))

        tool_placeholder.empty()

    # Save updated conversation after every agent response
    if st.session_state.current_run_id and st.session_state.current_labels:
        save_conversation(
            run_id=st.session_state.current_run_id,
            source_a=st.session_state.current_labels[0],
            source_b=st.session_state.current_labels[1],
            messages=st.session_state.messages,
            summary=st.session_state.current_results.get("summary", {}) if st.session_state.current_results else {}
        )

    st.rerun()


# ── Chat input ─────────────────────────────────────────────────────────────────
user_input = st.chat_input("Give the agent an instruction...")
if user_input:
    # Check for chart keywords
    chart_keywords = ["pie", "chart", "graph", "visual", "plot", "visualize"]
    if any(k in user_input.lower() for k in chart_keywords):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": "📊 Rendering charts from current reconciliation data."})
        st.session_state.show_pie_charts = True
        # Save conversation on chart request too
        if st.session_state.current_run_id and st.session_state.current_labels:
            save_conversation(
                run_id=st.session_state.current_run_id,
                source_a=st.session_state.current_labels[0],
                source_b=st.session_state.current_labels[1],
                messages=st.session_state.messages,
                summary=st.session_state.current_results.get("summary", {}) if st.session_state.current_results else {}
            )
    else:
        st.session_state.pending_instruction = user_input
    st.rerun()
